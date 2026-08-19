"""Centralized application configuration.

All runtime configuration is loaded from environment variables (optionally
via a local .env file). Nothing in this project should read os.environ
directly outside of this module -- import ``get_settings`` instead.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, populated from the environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    gemini_embedding_model: str = "gemini-embedding-001"

    # Chat engine
    max_chat_history: int = 20
    max_tool_calls: int = 5

    # Persistence
    chat_db_path: str = "data/chat_history.db"
    rag_db_path: str = "data/rag.db"

    # Retrieval-augmented generation
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 150
    rag_top_k: int = 5
    max_upload_size_mb: int = 10


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the .env file is only parsed once per process. Tests can
    bypass this by monkeypatching/patching ``get_settings`` directly.
    """
    return Settings()
