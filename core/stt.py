"""Speech-to-text, powered by Gemini's native multimodal audio understanding
(no separate STT provider needed -- Gemini accepts audio input directly).

Provider-specific logic is isolated here; nothing else in the app should
build Gemini audio requests directly.
"""

from __future__ import annotations

import logging

from google.genai import types

from core.exceptions import SpeechTranscriptionError
from core.gemini_client import get_client
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Formats Gemini is documented to accept for audio understanding.
_SUPPORTED_MIME_TYPES = {
    "audio/wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
    "audio/ogg",
    "audio/flac",
    "audio/aiff",
}

_TRANSCRIBE_INSTRUCTION = "Transcribe this audio verbatim. Return only the transcript text, nothing else."


async def transcribe(audio_bytes: bytes, mime_type: str | None = None) -> str:
    """Transcribe raw audio bytes into plain text using Gemini.

    Args:
        audio_bytes: raw uploaded audio content. Rejected if empty.
        mime_type: the audio's MIME type (e.g. "audio/wav", "audio/webm").
            Gemini requires a MIME type to correctly decode the audio, and
            it cannot be reliably inferred from raw bytes alone, so this
            optional parameter was added to the requested signature
            (defaults to "audio/wav" if not given -- see final summary).

    Raises:
        SpeechTranscriptionError: on empty input or provider failure.
    """
    if not audio_bytes:
        raise SpeechTranscriptionError("Audio data must not be empty.")

    resolved_mime_type = mime_type or "audio/wav"
    if resolved_mime_type not in _SUPPORTED_MIME_TYPES:
        logger.warning(
            "Unrecognized audio mime type '%s'; attempting transcription anyway.",
            resolved_mime_type,
        )

    client = get_client()
    settings = get_settings()

    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=resolved_mime_type),
                        types.Part.from_text(text=_TRANSCRIBE_INSTRUCTION),
                    ],
                )
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Speech transcription request failed: %s", exc)
        raise SpeechTranscriptionError("Speech transcription failed.") from exc

    text = _extract_text(response)
    if not text:
        raise SpeechTranscriptionError("Transcription produced no usable text.")
    return text


def _extract_text(response) -> str:
    candidates = getattr(response, "candidates", None)
    if not candidates or candidates[0].content is None or not candidates[0].content.parts:
        return ""
    return "".join(
        part.text for part in candidates[0].content.parts if getattr(part, "text", None)
    ).strip()
