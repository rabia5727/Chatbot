"""
Speech-to-text: turn recorded audio bytes into text.

Owner: Ghanwa

Integration contract:
- transcribe(audio_bytes) is the only function ui/voice_input.py calls.
  Keep the signature stable so Ifreen's mic widget doesn't need changes
  if you swap the underlying STT library.
"""


def transcribe(audio_bytes: bytes) -> str:
    """
    Convert recorded audio (bytes, e.g. WAV from the mic widget) to text.

    TODO(Ghanwa): implement using SpeechRecognition (or Gemini's audio
    input if you'd rather skip a separate STT library).
    """
    raise NotImplementedError("Ghanwa: implement STT")
