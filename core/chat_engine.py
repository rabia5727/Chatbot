"""
Conversation orchestration: takes user text, talks to Gemini, resolves
any tool/function calls Gemini asks for, and returns the final reply.

Owner: Ghanwa

Integration contract (don't change without telling Rabia/Ifreen):
- Reads the tool list from tools.tool_registry.get_tool_declarations()
  and dispatches calls via tools.tool_registry.dispatch(name, args).
- Reads/writes chat history via db.chat_history.get_history(user_id) /
  save_message(user_id, role, content) — Ifreen's UI never talks to the
  DB directly, it always goes through this module.
- send_message() is the one function app.py calls per user turn.
"""

from core.gemini_client import get_model
from core.prompts import SYSTEM_PROMPT
from tools.tool_registry import get_tool_declarations, dispatch


def send_message(user_id: str, user_text: str) -> str:
    """
    Send `user_text` to Gemini for `user_id`, resolve any tool calls,
    persist both turns, and return the assistant's final text reply.

    TODO(Ghanwa):
    1. Load prior history for user_id (db.chat_history.get_history).
    2. Start/continue a chat session with SYSTEM_PROMPT + history +
       get_tool_declarations().
    3. Send user_text; if Gemini responds with a function_call, run it
       through tools.tool_registry.dispatch(name, args) and send the
       result back to Gemini to get the final natural-language answer.
    4. Save both the user turn and assistant turn via
       db.chat_history.save_message().
    5. Return the assistant's text.
    """
    raise NotImplementedError("Ghanwa: implement Gemini call + function-calling loop")
