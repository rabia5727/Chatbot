"""Persistent chat history backed by a local SQLite file.

Chosen per project requirements: no external database service, just a
simple local file that works out of the box. sqlite3 is synchronous, so
every call is offloaded to a thread via ``asyncio.to_thread`` to avoid
blocking the event loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from config.settings import get_settings
from core.exceptions import ChatHistoryError

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _connect():
    """Open a connection to the configured SQLite file, creating the table
    (and parent directory) if needed. Commits on successful exit."""
    db_path = get_settings().chat_db_path
    parent_dir = os.path.dirname(db_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        yield conn
        conn.commit()
    finally:
        conn.close()


def _add_message_sync(user_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.now(timezone.utc).isoformat()),
        )


def _get_recent_messages_sync(user_id: str, limit: int) -> list[dict[str, Any]]:
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT role, content FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = cursor.fetchall()
    # rows come back newest-first; return oldest-first for building a
    # chronological conversation.
    return [{"role": role, "content": content} for role, content in reversed(rows)]


async def add_message(user_id: str, role: str, content: str) -> None:
    """Persist a single message. ``role`` should be ``"user"`` or ``"assistant"``."""
    try:
        await asyncio.to_thread(_add_message_sync, user_id, role, content)
    except sqlite3.Error as exc:
        logger.error("Failed to save message for user %s: %s", user_id, exc)
        raise ChatHistoryError("Could not save chat message.") from exc


async def get_recent_messages(user_id: str, limit: int) -> list[dict[str, Any]]:
    """Return up to ``limit`` most recent messages for ``user_id``, oldest first."""
    try:
        return await asyncio.to_thread(_get_recent_messages_sync, user_id, limit)
    except sqlite3.Error as exc:
        logger.error("Failed to load messages for user %s: %s", user_id, exc)
        raise ChatHistoryError("Could not load chat history.") from exc
