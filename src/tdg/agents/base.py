import abc
import importlib
import inspect
import json
import textwrap
from pathlib import Path
from typing import Optional, Literal, Callable, Any, Union

import aiofiles
import openai
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, Field

from tdg import parsing
from tdg.config import Settings
from tdg.extract import UndefinedFinder
from tdg.parse_humaneval import HEPSuite
from tdg.parsing import find_gen_signatures, nl_join

MAX_ITER_PER_AGENT = 5
MAX_HISTORY_PER_AGENT: int = 3 + (2 * MAX_ITER_PER_AGENT)
"""Limit the number of generations a given agent can do."""


class CodeContext:
    def __init__(self, test: Union[HEPSuite, Callable[[Any], Any]]):
        """

        Two input cases:
            HEPItem(): Prompt is coming from our benchmark, derived from HumanEval. Does NOT conform to our specs.
            callable(): We've passed in a test object, meaning it's coming from our Generator pipeline.


        """
        match test:
            case HEPSuite():
                # incoming from human eval
                self.test_sources = test.tests
                self.fn_names = [test.fn_name]
                self.signatures = [test.prompt]
                self.undefined = []

            case _:
                test_module = importlib.import_module(test.__module__)
                test_globals = vars(test_module)
                prior_frame = inspect.currentframe().f_back
                test_locals = prior_frame.f_locals

                self.test_sources = [inspect.getsource(test).replace(test.__doc__, "")]

                undefined = (
                    UndefinedFinder(test_globals, test_locals)
                    .visit_code(test)
                    .undefined
                )
                signatures = find_gen_signatures(test.__doc__)

                self.fn_names = list(signatures.keys())
                self.signatures = []
                self.undefined = []

                for idx, undefined in enumerate(undefined):
                    if sig := signatures.get(undefined):
                        self.signatures.append(
                            nl_join(
                                f"{idx}. Signature for function '{undefined}':",
                                textwrap.indent(sig, "\t"),
                                "----------",
                            )
                        )
                    else:
                        self.undefined.append(undefined)


class AgentConfig(BaseModel):
    model: str = "gpt-4-turbo-preview"
    temperature: Optional[float] = None
    frequency_penalty: Optional[float] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = None
    presence_penalty: Optional[float] = None
    seed: Optional[int] = None
    stream: Optional[Literal[False]] | Literal[True] = False
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = None

    def non_null(self) -> dict:
        return {k: v for k, v in self.dict().items() if v is not None}


class Message(BaseModel):
    role: str
    content: str

    @classmethod
    def user(cls, content: str):
        return cls(role="user", content=content)

    @classmethod
    def system(cls, content: str):
        return cls(role="system", content=content)

    @classmethod
    def assistant(cls, content: str):
        return cls(role="assistant", content=content)


class GenerationHistory(BaseModel):
    memory: dict[str, Message] = Field(default_factory=dict)
    """Mapping of user messages to remembered system messages"""

    messages: list[Message]
    """The entire message chain"""

    def messages_dict(self) -> list[dict[str, str]]:
        return [item.dict() for item in self.messages]

    def alter_initial(self, content: str):
        self.messages[2].content = content
        self.messages = self.messages[:3]


class MaxIterExceeded(BaseException):
    pass


class Agent(abc.ABC):
    """Agent interface for multiagent generation."""

    def __init__(
        self, config: Optional[AgentConfig] = None, pipeline_id: str = "no_id"
    ):
        self.client = openai.AsyncClient(
            api_key=Settings.from_dotenv().OPENAI_API_KEY.get_secret_value()
        )
        self.config = config or AgentConfig()
        self.pipeline_id = pipeline_id

        self.history = GenerationHistory.model_validate(
            {
                "messages": [
                    {"role": "system", "content": self.system_prompt()},
                ]
            }
        )

    @abc.abstractmethod
    def system_prompt(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def user_prompt(self) -> str:
        raise NotImplementedError()

    @property
    def cache_key(self) -> str:
        return self.__class__.__name__.lower().replace("agent", "") + "_history"

    @property
    def cache_file(self) -> Path:
        return Path.home() / ".tdg" / self.pipeline_id / f"{self.cache_key}.json"

    async def save_state(self):
        self.cache_file.parent.mkdir(exist_ok=True, parents=True)
        async with aiofiles.open(self.cache_file, "w") as f:
            await f.write(self.history.json())

    async def load_state(self):
        if self.cache_file.is_file():
            async with aiofiles.open(self.cache_file, "r") as f:
                content = await f.read()
                content = json.loads(content)
                self.history = GenerationHistory.model_validate(content)

    async def _communicate_with_openai(self, message: str) -> Message:
        # error if too many iterations
        if len(self.history.messages) > MAX_HISTORY_PER_AGENT:
            raise MaxIterExceeded(
                f"Agent {self.__class__.__name__} has exceeded its generation length of {MAX_HISTORY_PER_AGENT}"
            )

        # return from memory if exists!
        response = self.history.memory.get(message)
        if not response:
            # else, generate

            # create user a message object
            user_message = Message.user(message)
            # store it
            self.history.messages.append(user_message)

            # send the updated message history (user message last!) to LLM
            result: ChatCompletion = await self.client.chat.completions.create(
                messages=self.history.messages_dict(),
                **self.config.non_null(),
            )

            # for now, just pick the first option
            # TODO: search over multiple options
            choice = result.choices[0]
            response = Message(role=choice.message.role, content=choice.message.content)

            # add LLM response to message history
            self.history.messages.append(response)

            # remember user -> llm response chain
            self.history.memory[message] = response
            print(response.content)

            await self.save_state()

        return await self.ensure_output_valid(response)

    @abc.abstractmethod
    async def ensure_output_valid(self, message: Message):
        """Validate the message, returning if good, recursing back to generate again if not."""
        raise NotImplementedError()

    @property
    def response_key(self):
        return self.__class__.__name__.lower().replace("agent", "") + "_response"

    async def generate(self, message: str) -> Message:
        """Continue generation with openai."""

        result = await self._communicate_with_openai(message)

        return result


class CodeAgent(Agent):
    """
    An Agent Subclass that generates code.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.imports: list[str] = []

    async def ensure_output_valid(self, message: Message):
        return await self.ensure_valid_code(message)

    async def ensure_valid_code(self, choice: Message) -> Message:
        try:
            choice.content = parsing.clean_openai_code_or_error(choice.content)
        except SyntaxError:
            return await self.generate(
                "Your generation contained invalid python syntax. Please try again.",
            )

        good_imports, bad_imports = parsing.extract_and_filter_imports(choice.content)
        if bad_imports:
            return await self.generate(
                nl_join(
                    "Your generation imported libraries or modules that are not",
                    "available on our system:",
                    nl_join(*bad_imports),
                    "Please alter or remove the affected code.",
                )
            )

        self.imports = good_imports

        return choice
