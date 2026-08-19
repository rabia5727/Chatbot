"""
Main Streamlit entry point. Wires together everyone's modules —
this is the integration file, owned jointly (Ifreen maintains it, but
anyone can add a small hook once their piece is ready).

Run with: streamlit run app.py
"""

import streamlit as st

from config import APP_NAME
from core.chat_engine import send_message
from db.chat_history import get_history
from ui.audio_output import play_reply
from ui.chat_ui import render_history
from ui.sidebar import render_sidebar
from ui.styles import inject_custom_css
from ui.voice_input import record_and_transcribe

st.set_page_config(page_title=APP_NAME, page_icon="💬")
inject_custom_css()
render_sidebar()

st.title(APP_NAME)

# TODO: once db.auth is wired up, use the real logged-in user's id.
user_id = st.session_state.get("user", {}).get("id", "demo-user")

if "messages" not in st.session_state:
    # TODO(Ghanwa/Rabia): once get_history is implemented, load from
    # Supabase here instead of starting empty each run.
    st.session_state.messages = []

render_history(st.session_state.messages)

col_text, col_mic = st.columns([5, 1])
with col_mic:
    voice_text = record_and_transcribe()

typed_text = st.chat_input("Type a message...")
user_text = typed_text or voice_text

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = send_message(user_id, user_text)
        st.markdown(reply)
        play_reply(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
