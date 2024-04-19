import abc
import importlib
import inspect
import json
import textwrap
from pathlib import Path
from typing import Optional, Literal, Callable, Any

import aiofiles
import openai
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from tdg import parsing
from tdg.config import Settings
from tdg.extract import UndefinedFinder
from tdg.parsing import find_gen_signatures, nl_join


class CodeContext:
    def __init__(self, test: Callable[[Any], Any]):
        test_module = importlib.import_module(test.__module__)
        test_globals = vars(test_module)
        prior_frame = inspect.currentframe().f_back
        test_locals = prior_frame.f_locals

        self.test_fn = test
        self.test_source = inspect.getsource(test)
        self.test_source = self.test_source.replace(test.__doc__, "")

        undefined = (
            UndefinedFinder(test_globals, test_locals).visit_code(test).undefined
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


class GenerationHistory(BaseModel):
    messages: list[Message]
    """The entire message chain"""

    initial_response: Optional[Message] = None
    """The initial LLM response (result of agent.initial_generation)"""

    latest_response: Optional[Message] = None
    """The latest LLM response (result of agent.continue_generation)"""

    def messages_dict(self) -> list[dict[str, str]]:
        return [item.dict() for item in self.messages]

    def alter_initial(self, content: str):
        self.initial_response.content = content
        self.messages[2] = self.initial_response
        self.messages = self.messages[:3]


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

        self.history = GenerationHistory(messages=[])

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

    async def _communicate_with_openai(
        self, phase: Literal["initial", "latest"]
    ) -> Message:
        if response := getattr(self.history, f"{phase}_response"):
            return response
        else:
            result: ChatCompletion = await self.client.chat.completions.create(
                messages=self.history.messages_dict(),
                **self.config.non_null(),
            )
            choice = result.choices[0]
            message = Message(role=choice.message.role, content=choice.message.content)
            self.history.messages.append(message)
            setattr(self.history, f"{phase}_response", message)
            await self.save_state()

        return message

    async def _do_initial_generation(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Message:
        """Do the initial Agent generation.

        Will RESET self.message_history if any exists. For subsequent communication with the same system,
        please use self.continue_generation().
        """

        if not self.history.messages:
            self.history = GenerationHistory.model_validate(
                {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                }
            )

        result = await self._communicate_with_openai(phase="initial")

        return result

    @property
    def response_key(self):
        return self.__class__.__name__.lower().replace("agent", "") + "_response"

    async def initial_generation(self) -> Message:
        result = await self._do_initial_generation(
            system_prompt=self.system_prompt(),
            user_prompt=self.user_prompt(),
        )
        return result

    async def continue_generation(self, message: str) -> Message:
        self.history.latest_response = None
        self.history.messages.append(
            Message(
                role="user",
                content=message,
            )
        )
        result = await self._communicate_with_openai(phase="latest")

        return result


class CodeAgent(Agent):
    """
    An Agent Subclass that generates code.
    """

    async def initial_generation(self) -> Message:
        """
        Generate a response and ensure it is valid python code.

        Returns:
            Valid python code.
        """
        choice = await self._do_initial_generation(
            system_prompt=self.system_prompt(),
            user_prompt=self.user_prompt(),
        )

        choice.content = parsing.clean_openai_code_or_error(choice.content)
        return choice
