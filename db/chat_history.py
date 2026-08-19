"""
Persist and retrieve chat messages from Supabase.

Owner: Rabia

Integration contract:
- core/chat_engine.py is the ONLY caller of these — the UI layer never
  touches this file directly. Keep signatures stable.

Note: db/schema.sql enables Row Level Security, so these calls only
succeed for an authenticated session (see db/auth.py's set_session) —
the signed-in user can only read/write their own rows.
"""

from db.supabase_client import supabase


def save_message(user_id: str, role: str, content: str) -> None:
    """Insert one row into `messages` (see db/schema.sql). role is "user" or "assistant"."""
    supabase.table("messages").insert(
        {"user_id": user_id, "role": role, "content": content}
    ).execute()


def get_history(user_id: str, limit: int = 50) -> list[dict]:
    """
    Return the last `limit` messages for user_id, oldest first, as
    [{"role": ..., "content": ...}, ...] — the shape core/chat_engine.py
    feeds back into Gemini.
    """
    response = (
        supabase.table("messages")
        .select("role, content, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data or []
    rows.reverse()
    return [{"role": row["role"], "content": row["content"]} for row in rows]
