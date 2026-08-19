"""
Mic recording widget -> hands audio bytes to core.stt for transcription.

Owner: Ifreen

Integration contract:
- record_and_transcribe() returns the transcribed text (or None if the
  user didn't record anything), using core.stt.transcribe (Ghanwa) to
  do the actual conversion. This file only owns the widget/UX.
"""

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from core.stt import transcribe


def record_and_transcribe() -> str | None:
    audio_bytes = audio_recorder()
    if not audio_bytes:
        return None
    with st.spinner("Transcribing..."):
        return transcribe(audio_bytes)
