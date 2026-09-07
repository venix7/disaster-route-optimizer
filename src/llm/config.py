import os
from dataclasses import dataclass

from dotenv import load_dotenv


class AssistantConfigurationError(RuntimeError):
    """Raised when the Groq assistant is not configured."""


@dataclass(frozen=True)
class GroqSettings:
    """
    Backend-only Groq configuration.

    The API key is never included in an API response or sent to
    the React application.
    """

    api_key: str | None
    model: str
    timeout_seconds: int
    max_tool_rounds: int

    @classmethod
    def from_environment(cls):

        load_dotenv()

        return cls(
            api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-20b"
            ),
            timeout_seconds=cls._read_positive_integer(
                "GROQ_TIMEOUT_SECONDS",
                30
            ),
            max_tool_rounds=cls._read_positive_integer(
                "ASSISTANT_MAX_TOOL_ROUNDS",
                4
            )
        )

    @property
    def is_configured(self):

        return bool(
            self.api_key
            and self.api_key.strip()
        )

    def require_api_key(self):

        if not self.is_configured:

            raise AssistantConfigurationError(
                "GROQ_API_KEY is not configured."
            )

        return self.api_key.strip()

    @staticmethod
    def _read_positive_integer(
        variable_name,
        default
    ):

        raw_value = os.getenv(
            variable_name
        )

        if raw_value is None:
            return default

        try:
            value = int(raw_value)
        except ValueError:
            return default

        return value if value > 0 else default


def create_groq_chat_model(settings):
    """
    Create the LangChain Groq chat model lazily.

    Lazy creation allows every existing deterministic endpoint to
    keep working even when the optional assistant key is absent.
    """

    from langchain_groq import (
        ChatGroq
    )

    return ChatGroq(
        model=settings.model,
        api_key=settings.require_api_key(),
        timeout=settings.timeout_seconds,
        max_retries=2
    )
