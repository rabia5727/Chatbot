from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core import tts
from core.exceptions import SpeechSynthesisError


async def test_synthesize_rejects_blank_text():
    with pytest.raises(SpeechSynthesisError):
        await tts.synthesize("   ")


async def test_synthesize_handles_provider_failure():
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("boom"))

    with patch("core.tts.get_client", return_value=fake_client):
        with pytest.raises(SpeechSynthesisError):
            await tts.synthesize("hello")


async def test_synthesize_raises_when_no_audio_returned():
    fake_content = SimpleNamespace(parts=[])
    fake_candidate = SimpleNamespace(content=fake_content)
    fake_response = SimpleNamespace(candidates=[fake_candidate])

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    with patch("core.tts.get_client", return_value=fake_client):
        with pytest.raises(SpeechSynthesisError):
            await tts.synthesize("hello world")


async def test_synthesize_returns_mp3_bytes_on_success():
    # NOTE: this test exercises the real PCM->MP3 conversion path and
    # therefore requires ffmpeg to be installed and on PATH (pydub shells
    # out to it). See final summary for this dependency.
    silence_pcm = b"\x00\x00" * 2400  # 0.1s of silence at 24kHz/16-bit/mono
    inline_data = SimpleNamespace(data=silence_pcm)
    fake_part = SimpleNamespace(inline_data=inline_data)
    fake_content = SimpleNamespace(parts=[fake_part])
    fake_candidate = SimpleNamespace(content=fake_content)
    fake_response = SimpleNamespace(candidates=[fake_candidate])

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    with patch("core.tts.get_client", return_value=fake_client):
        audio_bytes = await tts.synthesize("hello world")

        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
