"""SQLite persistence for uploaded document metadata."""

from __future__ import annotations

import asyncio
import contextlib
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from config.settings import get_settings


@contextlib.contextmanager
def connect():
    db_path = get_settings().rag_db_path
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            chunk_count INTEGER NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id)")
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
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_sync(metadata: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """INSERT INTO documents
               (document_id, user_id, filename, mime_type, uploaded_at, chunk_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                metadata["document_id"], metadata["user_id"], metadata["filename"],
                metadata["mime_type"], metadata.get("uploaded_at") or datetime.now(timezone.utc).isoformat(),
                metadata["chunk_count"],
            ),
        )


def _list_sync(user_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT document_id, filename, mime_type, uploaded_at, chunk_count
               FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC""",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _get_sync(document_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
    return dict(row) if row else None


def _delete_sync(document_id: str, user_id: str) -> bool:
    with connect() as conn:
        owner = conn.execute(
            "SELECT 1 FROM documents WHERE document_id = ? AND user_id = ?", (document_id, user_id)
        ).fetchone()
        if not owner:
            return False
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        return True


async def create_document(metadata: dict[str, Any]) -> None:
    await asyncio.to_thread(_create_sync, metadata)


async def list_documents(user_id: str) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_sync, user_id)


async def get_document(document_id: str) -> dict[str, Any] | None:
    return await asyncio.to_thread(_get_sync, document_id)


async def delete_document(document_id: str, user_id: str) -> bool:
    return await asyncio.to_thread(_delete_sync, document_id, user_id)
