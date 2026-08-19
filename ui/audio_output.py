"""
Plays back the assistant's reply as speech using core.tts.

Owner: Ifreen
"""

import streamlit as st

from core.tts import synthesize


def play_reply(text: str) -> None:
    audio_bytes = synthesize(text)
    st.audio(audio_bytes, format="audio/mp3")
