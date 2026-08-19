"""Persistent chat history, backed by Supabase (the `messages` table from
db/schema.sql).

Owner: Rabia (storage) / Ghanwa (async contract — core/chat_engine.py is
the only caller)

supabase-py is a blocking client, so every call is offloaded to a thread
via asyncio.to_thread to avoid blocking the event loop — same pattern
core/chat_engine.py already uses elsewhere.

Note: db/schema.sql enables Row Level Security, so these calls only
succeed for an authenticated session (see db/auth.py's set_session) —
the signed-in user can only read/write their own rows.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.exceptions import ChatHistoryError
from db.supabase_client import supabase

logger = logging.getLogger(__name__)


def _add_message_sync(user_id: str, role: str, content: str) -> None:
    supabase.table("messages").insert(
        {"user_id": user_id, "role": role, "content": content}
    ).execute()


def _get_recent_messages_sync(user_id: str, limit: int) -> list[dict[str, Any]]:
    response = (
        supabase.table("messages")
        .select("role, content, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data or []
    rows.reverse()  # oldest first, for building a chronological conversation
    return [{"role": row["role"], "content": row["content"]} for row in rows]


async def add_message(user_id: str, role: str, content: str) -> None:
    """Persist a single message. `role` should be "user" or "assistant"."""
    try:
        await asyncio.to_thread(_add_message_sync, user_id, role, content)
    except Exception as exc:
        logger.error("Failed to save message for user %s: %s", user_id, exc)
        raise ChatHistoryError("Could not save chat message.") from exc


async def get_recent_messages(user_id: str, limit: int) -> list[dict[str, Any]]:
    """Return up to `limit` most recent messages for user_id, oldest first."""
    try:
        return await asyncio.to_thread(_get_recent_messages_sync, user_id, limit)
    except Exception as exc:
        logger.error("Failed to load messages for user %s: %s", user_id, exc)
        raise ChatHistoryError("Could not load chat history.") from exc
