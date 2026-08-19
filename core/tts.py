"""
Text-to-speech: turn the assistant's reply text into playable audio.

Owner: Ghanwa

Integration contract:
- synthesize(text) is the only function ui/audio_output.py calls, and
  must return raw audio bytes (e.g. mp3) that st.audio() can play.
"""


def synthesize(text: str) -> bytes:
    """
    Convert `text` to speech audio bytes.

    TODO(Ghanwa): implement using gTTS (simplest) or another TTS engine.
    Return bytes, not a file path — ui/audio_output.py plays it directly
    with st.audio(audio_bytes).
    """
    raise NotImplementedError("Ghanwa: implement TTS")
