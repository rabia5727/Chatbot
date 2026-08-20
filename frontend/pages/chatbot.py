"""
Screen 4 — Chatbot

The main application screen. Only the message list scrolls internally
(via st.container(height=...)); the header stays pinned at the top and
the message composer stays pinned at the bottom, so the page itself
never scrolls.
"""

from datetime import datetime
import streamlit as st
from components.sidebar import render_sidebar
from components.header import render_header
from components.chat_message import render_user_message, render_assistant_message
from components.icons import chat, cloud, document
from components.ui_components import (
    logo_mark,
    typing_indicator,
    voice_listening_indicator,
    tts_playing_indicator,
)
from utils.backend import send_chat_message, upload_document

SUGGESTED_PROMPTS = [
    (document(22), "Ask about a document"),
    (cloud(22), "Check the weather"),
    (chat(22), "Ask anything"),
]

MESSAGE_LIST_HEIGHT = 440


def _ensure_state() -> None:
    defaults = {
        "chat_history": [
            {
                "role": "user",
                "content": "Can you summarize this document?",
                "time": "10:30 AM",
            },
            {
                "role": "assistant",
                "payload": {
                    "type": "rag",
                    "source": "project_document.pdf",
                    "answer": "Sure! Here is a summary of the document you uploaded.",
                },
                "time": "10:31 AM",
            },
        ],
        "active_conversation": "Project Summary",
        "pending_message": None,
        "pending_file": None,
        "voice_listening": False,
        "tts_playing_index": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render() -> None:
    _ensure_state()
    render_sidebar()

    with st.container(key="chat_main_container"):
        render_header()

        if not st.session_state.chat_history:
            _render_empty_state()
        else:
            _render_chat_history()

        _render_input_row()

        if st.session_state.pending_message:
            _process_pending_message()


def _render_empty_state() -> None:
    user = st.session_state.get("user") or {"name": "Ifreen"}
    first_name = user.get("name", "Ifreen").split(" ")[0]

    with st.container(height=MESSAGE_LIST_HEIGHT, border=False):
        st.markdown('<div class="empty-state-wrap">', unsafe_allow_html=True)
        logo_mark(size=44, centered=True)
        st.markdown(f'<div class="empty-state-greeting">Hello, {first_name}!</div>', unsafe_allow_html=True)
        st.markdown('<div class="empty-state-sub">How can I help you today?</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        cols = st.columns(len(SUGGESTED_PROMPTS), gap="small")
        for col, (icon, prompt) in zip(cols, SUGGESTED_PROMPTS):
            with col:
                st.markdown(
                    f"""
                    <div class="prompt-suggestion-card">
                        <div class="prompt-icon">{icon}</div>
                        <div class="prompt-text">{prompt}</div>
                        <div class="prompt-arrow">›</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Use Prompt", key=f"suggested_{prompt}", use_container_width=True):
                    st.session_state.pending_message = prompt
                    st.rerun()


def _render_chat_history() -> None:
    with st.container(height=MESSAGE_LIST_HEIGHT, border=False):
        for i, turn in enumerate(st.session_state.chat_history):
            if turn["role"] == "user":
                render_user_message(turn["content"], timestamp=turn.get("time", ""))
            else:
                render_assistant_message(turn["payload"], timestamp=turn.get("time", ""))
                if st.session_state.tts_playing_index == i:
                    tts_playing_indicator()
                else:
                    if st.button("Play response", icon=":material/volume_up:", key=f"tts_{i}"):
                        st.session_state.tts_playing_index = i
                        st.rerun()


def _render_input_row() -> None:
    st.markdown('<div class="composer-outer-wrap">', unsafe_allow_html=True)
    col_attach, col_mic, col_input = st.columns([1, 1, 12], gap="small")

    with col_attach:
        with st.popover("", icon=":material/attach_file:", use_container_width=True):
            uploaded = st.file_uploader(
                "Upload a document",
                type=["pdf", "docx", "txt"],
                label_visibility="collapsed",
                key="file_uploader",
            )
            if uploaded is not None:
                result = upload_document(uploaded)
                if result["success"]:
                    st.session_state.pending_file = uploaded
                    st.caption(f"Ready to reference: **{result['filename']}**")

    with col_mic:
        if st.button("", icon=":material/mic:", key="mic_button", help="Voice input (UI demo only)"):
            st.session_state.voice_listening = not st.session_state.voice_listening
            st.rerun()

    with col_input:
        typed = st.chat_input("Type your message...")
        if typed:
            st.session_state.pending_message = typed

    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.voice_listening:
        voice_col1, voice_col2 = st.columns([3, 1])
        with voice_col1:
            voice_listening_indicator()
        with voice_col2:
            if st.button("Stop listening", key="stop_listening"):
                st.session_state.voice_listening = False
                st.session_state.pending_message = "What's the weather like today?"
                st.rerun()


def _process_pending_message() -> None:
    message = st.session_state.pending_message
    st.session_state.pending_message = None
    now = datetime.now().strftime("%I:%M %p").lstrip("0")

    st.session_state.chat_history.append({"role": "user", "content": message, "time": now})

    placeholder = st.empty()
    with placeholder.container():
        typing_indicator()

    payload = send_chat_message(message, uploaded_file=st.session_state.pending_file)
    placeholder.empty()

    st.session_state.chat_history.append({"role": "assistant", "payload": payload, "time": now})
    st.session_state.pending_file = None
    st.rerun()
