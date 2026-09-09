from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ai_provider: Literal["openai", "ollama"] = "openai"
    openai_api_key: str | None = None
    provider_api_key: str | None = None
    provider_base_url: str | None = None
    codebase_root: Path = Path(".")
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "codebase_chunks"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4.1-mini"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
