"""
Renders the chat message history and input box.

Owner: Ifreen

Integration contract:
- render_history(messages) draws {"role", "content"} dicts (same shape
  db.chat_history.get_history returns) — doesn't know anything about
  Gemini or Supabase.
"""

import streamlit as st


def render_history(messages: list[dict]) -> None:
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
