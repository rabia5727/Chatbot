"""Text-to-speech, powered by Gemini's native TTS models.

Gemini TTS returns raw PCM audio; this module wraps it as WAV in-memory
and re-encodes to MP3 via pydub (requires ffmpeg on PATH -- see final
summary for this dependency). Nothing is written to disk.
"""

from __future__ import annotations

import io
import logging
import wave

from google.genai import types
from pydub import AudioSegment

from core.exceptions import SpeechSynthesisError
from core.gemini_client import get_client
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Gemini TTS models return 24kHz, 16-bit, mono PCM.
_SAMPLE_RATE_HZ = 24000
_SAMPLE_WIDTH_BYTES = 2
_CHANNELS = 1
_VOICE_NAME = "Kore"


async def synthesize(text: str) -> bytes:
    """Convert ``text`` into MP3 audio bytes using Gemini TTS.

    Raises:
        SpeechSynthesisError: on blank input or provider/encoding failure.
    """
    if not text or not text.strip():
        raise SpeechSynthesisError("Text to synthesize must not be empty.")

    client = get_client()
    settings = get_settings()

    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_tts_model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=_VOICE_NAME)
                    )
                ),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Speech synthesis request failed: %s", exc)
        raise SpeechSynthesisError("Speech synthesis failed.") from exc

    pcm_data = _extract_pcm_audio(response)
    if not pcm_data:
        raise SpeechSynthesisError("Synthesis produced no audio data.")

    return _pcm_to_mp3(pcm_data)


def _extract_pcm_audio(response) -> bytes:
    candidates = getattr(response, "candidates", None)
    if not candidates or candidates[0].content is None or not candidates[0].content.parts:
        return b""
    for part in candidates[0].content.parts:
        inline_data = getattr(part, "inline_data", None)
        if inline_data and getattr(inline_data, "data", None):
            return inline_data.data
    return b""


def _pcm_to_mp3(pcm_data: bytes) -> bytes:
    """Wrap raw PCM as an in-memory WAV, then transcode to MP3 in-memory."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(_CHANNELS)
        wav_file.setsampwidth(_SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(_SAMPLE_RATE_HZ)
        wav_file.writeframes(pcm_data)
    wav_buffer.seek(0)

    try:
        audio_segment = AudioSegment.from_wav(wav_buffer)
        mp3_buffer = io.BytesIO()
        audio_segment.export(mp3_buffer, format="mp3")
        return mp3_buffer.getvalue()
    except Exception as exc:  # noqa: BLE001
        logger.error("PCM-to-MP3 conversion failed (is ffmpeg installed and on PATH?): %s", exc)
        raise SpeechSynthesisError(
            "Failed to encode audio to MP3. Ensure ffmpeg is installed and on PATH."
        ) from exc
