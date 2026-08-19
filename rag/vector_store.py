"""Chunk/vector storage and Python cosine similarity search, backed by
Supabase (the `chunks` table from db/schema.sql).

Owner: Rabia (storage) / Ghanwa (cosine_similarity + retrieval contract,
used by rag/retriever.py)

Embeddings are stored as jsonb, so supabase-py returns them already
parsed as Python lists on read -- no manual JSON encode/decode needed.
"""

from __future__ import annotations

import asyncio
import math
from typing import Any

from db.supabase_client import supabase


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _store_sync(chunks: list[dict[str, Any]]) -> None:
    supabase.table("chunks").insert(
        [
            {
                "document_id": item["document_id"],
                "user_id": item["user_id"],
                "filename": item["filename"],
                "chunk_index": item["chunk_index"],
                "page": item.get("page"),
                "text": item["text"],
                "embedding": item["embedding"],
            }
            for item in chunks
        ]
    ).execute()


def _search_sync(
    user_id: str, query_vector: list[float], document_id: str | None, top_k: int
) -> list[dict[str, Any]]:
    query = (
        supabase.table("chunks")
        .select("document_id, filename, chunk_index, page, text, embedding")
        .eq("user_id", user_id)
    )
    if document_id:
        query = query.eq("document_id", document_id)
    rows = query.execute().data or []

    results = []
    for row in rows:
        item = dict(row)
        item["score"] = cosine_similarity(query_vector, item.pop("embedding"))
        results.append(item)
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


async def store_chunks(chunks: list[dict[str, Any]]) -> None:
    await asyncio.to_thread(_store_sync, chunks)


async def similarity_search(
    user_id: str, query_vector: list[float], document_id: str | None = None, top_k: int = 5
) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_search_sync, user_id, query_vector, document_id, top_k)
