"""Gemini embedding adapter with validated vector output."""

from __future__ import annotations

import logging

from google.genai import types

from config.settings import get_settings
from core.exceptions import EmbeddingError
from core.gemini_client import get_client

logger = logging.getLogger(__name__)


async def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    if not texts or any(not text.strip() for text in texts):
        raise EmbeddingError("Embedding input must contain non-empty text.")
    try:
        response = await get_client().aio.models.embed_content(
            model=get_settings().gemini_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        embeddings = getattr(response, "embeddings", None) or []
        vectors = [list(item.values or []) for item in embeddings]
        if len(vectors) != len(texts) or any(not vector for vector in vectors):
            raise EmbeddingError("The embedding provider returned incomplete vectors.")
        return vectors
    except EmbeddingError:
        raise
    except Exception as exc:
        logger.error("Embedding request failed: %s", exc)
        raise EmbeddingError("Could not create document embeddings.") from exc


async def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    return (await embed_texts([text], task_type=task_type))[0]
