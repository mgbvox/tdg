import os

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr


class Settings(BaseModel):
    OPENAI_API_KEY: SecretStr
    LLM_MODEL: str = "gpt-4-turbo-preview"

    @classmethod
    def from_dotenv(cls):
        load_dotenv()
        return cls.model_validate(os.environ)
