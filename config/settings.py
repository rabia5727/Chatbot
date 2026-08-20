"""Centralized application configuration.

All runtime configuration is loaded from environment variables (optionally
via a local .env file). Nothing in this project should read os.environ
directly outside of this module -- import ``get_settings`` instead.

Owner: Ghanwa (structure) / Rabia (Supabase fields)
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path, not "env_file=.env" -- a relative path resolves against
# the process's current working directory, which depends on how/where the
# app got launched (e.g. Streamlit run from a different cwd) and silently
# finds no .env at all in that case. This always finds the one next to
# the project root, regardless of launch method.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings, populated from the environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    gemini_embedding_model: str = "gemini-embedding-001"

    # Chat engine
    max_chat_history: int = 20
    max_tool_calls: int = 5

    # Retrieval-augmented generation
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 150
    rag_top_k: int = 5
    max_upload_size_mb: int = 10

    # Supabase (persistence for chat history, documents/RAG chunks, auth, face login)
    supabase_url: str = ""
    supabase_key: str = ""
    # service_role/secret key -- privileged, used only by db/face_auth.py to
    # match a login photo against every user's stored face. Never expose
    # this anywhere else (no UI, no logs, no committing it to git).
    supabase_service_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the .env file is only parsed once per process. Tests can
    bypass this by monkeypatching/patching ``get_settings`` directly.
    """
    return Settings()
