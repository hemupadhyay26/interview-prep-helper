from enum import Enum
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvMode(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    app_name: str = "pydantic-ai-agent"
    env_mode: EnvMode = EnvMode.DEVELOPMENT
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    openai_api_key: str
    llm_model_name: str = "gpt-5.2"
    # Smaller / cheaper model for lightweight side tasks (chat titles).
    # Unset -> falls back to llm_model_name (see app/agents/models.py).
    title_model_name: str | None = None
    embedding_model_name: str = "text-embedding-3-small"
    database_url: str = "sqlite+aiosqlite:///./data/prephelper.db"
    chroma_persist_dir: str = "./data/chroma"
    langfuse_enabled: bool = Field(
        default=False,
        validation_alias="LANGFUSE_ENABLED",
    )

    langfuse_public_key: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_PUBLIC_KEY",
    )

    langfuse_secret_key: str | None = Field(
        default=None,
        validation_alias="LANGFUSE_SECRET_KEY",
    )

    langfuse_base_url: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias="LANGFUSE_BASE_URL",
    )

    langfuse_environment: str = Field(
        default="development",
        validation_alias="LANGFUSE_TRACING_ENVIRONMENT",
    )


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()