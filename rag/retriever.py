"""User-scoped semantic retrieval over stored document chunks."""

from __future__ import annotations

from config.settings import get_settings
from core.exceptions import EmbeddingError, RetrievalError
from rag.embeddings import embed_text
from rag.vector_store import similarity_search


async def retrieve(
    user_id: str, query: str, document_id: str | None = None, top_k: int | None = None
) -> list[dict]:
    if not user_id.strip() or not query.strip():
        raise RetrievalError("A user ID and non-empty question are required.")
    limit = top_k if top_k is not None else get_settings().rag_top_k
    if limit <= 0:
        raise RetrievalError("top_k must be positive.")
    try:
        query_vector = await embed_text(query, task_type="RETRIEVAL_QUERY")
        return await similarity_search(user_id, query_vector, document_id=document_id, top_k=limit)
    except EmbeddingError:
        raise
    except Exception as exc:
        raise RetrievalError("Could not retrieve relevant document context.") from exc
