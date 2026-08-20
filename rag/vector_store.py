"""Storage integration contract and reusable vector similarity utility.

This module deliberately contains no storage implementation. The database
team can implement ``VectorStore`` and inject it into the RAG service.
"""

from __future__ import annotations

import math
from typing import Any, Protocol


class VectorStore(Protocol):
    """Backend contract required by document ingestion and retrieval."""

    async def store_document(
        self, metadata: dict[str, Any], chunks: list[dict[str, Any]]
    ) -> None: ...

    async def search_chunks(
        self,
        user_id: str,
        query_vector: list[float],
        document_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]: ...

    async def list_documents(self, user_id: str) -> list[dict[str, Any]]: ...

    async def delete_document(self, document_id: str, user_id: str) -> bool: ...


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity without depending on a storage backend."""
    if not left or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
