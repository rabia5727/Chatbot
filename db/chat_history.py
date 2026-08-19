"""
Persist and retrieve chat messages from Supabase.

Owner: Rabia

Integration contract:
- core/chat_engine.py is the ONLY caller of these — the UI layer never
  touches this file directly. Keep signatures stable.
"""

from db.supabase_client import supabase


def save_message(user_id: str, role: str, content: str) -> None:
    """
    TODO(Rabia): insert a row into `messages`
    (see db/schema.sql). `role` is "user" or "assistant".
    """
    raise NotImplementedError("Rabia: implement message save")


def get_history(user_id: str, limit: int = 50) -> list[dict]:
    """
    TODO(Rabia): return the last `limit` messages for user_id, oldest
    first, as a list of {"role": ..., "content": ...} dicts — that's the
    shape core/chat_engine.py expects to feed back into Gemini.
    """
    raise NotImplementedError("Rabia: implement history fetch")
