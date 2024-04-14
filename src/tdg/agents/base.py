import abc

import openai

from tdg.config import Settings


class Agent(abc.ABC):
    """Agent interface for multiagent generation."""

    def __init__(self):
        self.client = openai.AsyncClient(
            api_key=Settings.from_dotenv().OPENAI_API_KEY.get_secret_value()
        )

    @classmethod
    @abc.abstractmethod
    def system_prompt(cls) -> str:
        raise NotImplementedError()
