import abc
from typing import Optional, Literal

import openai
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from tdg import parsing
from tdg.agents.templates import nl_join
from tdg.config import Settings


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


class Agent(abc.ABC):
    """Agent interface for multiagent generation."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.client = openai.AsyncClient(
            api_key=Settings.from_dotenv().OPENAI_API_KEY.get_secret_value()
        )
        self.config = config or AgentConfig()

        self.gen_response: str = ""

    @abc.abstractmethod
    def system_prompt(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def user_prompt(self) -> str:
        raise NotImplementedError()

    # TODO: update cache to work with async coroutines!
    # @disk_cache
    # @staticmethod
    async def _do_generation(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> ChatCompletion:
        result = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **self.config.non_null(),
        )
        return result

    @abc.abstractmethod
    async def gen(self) -> str:
        raise NotImplementedError()


class CodeAgent(Agent):
    """
    An Agent Subclass that generates code.
    """

    async def gen(self) -> str:
        """
        Generate a response and ensure it is valid python code.

        Returns:
            Valid python code.
        """
        result: ChatCompletion = await self._do_generation(
            system_prompt=self.system_prompt(),
            user_prompt=self.user_prompt(),
        )
        content = result.choices[0].message.content
        clean = parsing.clean_openai_code(content)
        parsed, ast_or_error = parsing.is_valid_python(clean)
        if parsed:
            self.gen_response = clean
            return self.gen_response
        else:
            raise SyntaxError(
                nl_join(
                    "Invalid python code generated!",
                    content,
                )
            ) from ast_or_error
