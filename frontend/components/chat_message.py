"""
Renders a single chat turn (user or assistant), including the special
assistant UI states: normal reply, RAG reply, and weather-tool reply.
"""

import streamlit as st

from components.icons import document


def render_user_message(text: str, timestamp: str = "") -> None:
    with st.chat_message("user"):
        st.markdown(
            f'<div class="msg-bubble user">{text}</div>'
            f'<div class="msg-timestamp user">{timestamp} ✓</div>',
            unsafe_allow_html=True,
        )


def render_assistant_message(payload: dict, timestamp: str = "") -> None:
    """
    payload is one of the dict shapes returned by
    utils.backend.send_chat_message():
      {"type": "normal", "answer": str}
      {"type": "rag", "source": str, "answer": str}

    The "weather" shape below is unreachable now -- weather answers come
    back as plain text through Gemini's tool-calling (type "normal"),
    same as any other tool result. Left in case a structured weather
    card is wanted again later.
    """
    msg_type = payload.get("type", "normal")

    with st.chat_message("assistant"):
        if msg_type == "rag":
            st.markdown(
                f'<div class="msg-source-pill">{document(14)} Based on: {payload["source"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="msg-bubble assistant">{payload["answer"]}</div>'
                f'<div class="msg-timestamp">{timestamp}</div>',
                unsafe_allow_html=True,
            )

        elif msg_type == "weather":
            st.markdown(
                f"""
                <div class="weather-card">
                    <div class="weather-card-label">Weather</div>
                    <div class="weather-row"><span>Location</span><b>{payload['location']}</b></div>
                    <div class="weather-temp">{payload['temperature']}</div>
                    <div class="weather-row"><span>Condition</span><b>{payload['condition']}</b></div>
                    <div class="weather-row"><span>Humidity</span><b>{payload['humidity']}</b></div>
                </div>
                <div class="msg-timestamp">{timestamp}</div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f'<div class="msg-bubble assistant">{payload.get("answer", "")}</div>'
                f'<div class="msg-timestamp">{timestamp}</div>',
                unsafe_allow_html=True,
            )
