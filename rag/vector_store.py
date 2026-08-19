"""SQLite chunk/vector storage and Python cosine similarity search."""

from __future__ import annotations

import asyncio
import json
import math
from typing import Any

from db.documents import connect


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _ensure_chunks_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            page INTEGER,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
            UNIQUE(document_id, chunk_index)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_user_doc ON chunks(user_id, document_id)")


def _store_sync(chunks: list[dict[str, Any]]) -> None:
    with connect() as conn:
        _ensure_chunks_table(conn)
        conn.executemany(
            """INSERT INTO chunks
               (document_id, user_id, filename, chunk_index, page, text, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    item["document_id"], item["user_id"], item["filename"], item["chunk_index"],
                    item.get("page"), item["text"], json.dumps(item["embedding"], separators=(",", ":")),
                )
                for item in chunks
            ],
        )


def _search_sync(user_id: str, query_vector: list[float], document_id: str | None, top_k: int):
    with connect() as conn:
        _ensure_chunks_table(conn)
        sql = "SELECT document_id, filename, chunk_index, page, text, embedding FROM chunks WHERE user_id = ?"
        params: list[Any] = [user_id]
        if document_id:
            sql += " AND document_id = ?"
            params.append(document_id)
        rows = conn.execute(sql, params).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        item["score"] = cosine_similarity(query_vector, json.loads(item.pop("embedding")))
        results.append(item)
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


async def store_chunks(chunks: list[dict[str, Any]]) -> None:
    await asyncio.to_thread(_store_sync, chunks)


async def similarity_search(
    user_id: str, query_vector: list[float], document_id: str | None = None, top_k: int = 5
) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_search_sync, user_id, query_vector, document_id, top_k)
