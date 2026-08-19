from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core import stt
from core.exceptions import SpeechTranscriptionError


async def test_transcribe_rejects_empty_bytes():
    with pytest.raises(SpeechTranscriptionError):
        await stt.transcribe(b"")


async def test_transcribe_handles_provider_failure():
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("boom"))

    with patch("core.stt.get_client", return_value=fake_client):
        with pytest.raises(SpeechTranscriptionError):
            await stt.transcribe(b"fake-audio-bytes")


async def test_transcribe_returns_text_on_success():
    fake_part = SimpleNamespace(text="hello world")
    fake_content = SimpleNamespace(parts=[fake_part])
    fake_candidate = SimpleNamespace(content=fake_content)
    fake_response = SimpleNamespace(candidates=[fake_candidate])

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    with patch("core.stt.get_client", return_value=fake_client), patch(
        "core.stt.types.Part.from_bytes", return_value=SimpleNamespace()
    ), patch("core.stt.types.Part.from_text", return_value=SimpleNamespace()), patch(
        "core.stt.types.Content",
        side_effect=lambda role, parts: SimpleNamespace(role=role, parts=parts),
    ):
        result = await stt.transcribe(b"fake-audio-bytes", mime_type="audio/wav")

        assert result == "hello world"


async def test_transcribe_raises_when_no_text_returned():
    fake_content = SimpleNamespace(parts=[])
    fake_candidate = SimpleNamespace(content=fake_content)
    fake_response = SimpleNamespace(candidates=[fake_candidate])

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    with patch("core.stt.get_client", return_value=fake_client), patch(
        "core.stt.types.Part.from_bytes", return_value=SimpleNamespace()
    ), patch("core.stt.types.Part.from_text", return_value=SimpleNamespace()), patch(
        "core.stt.types.Content",
        side_effect=lambda role, parts: SimpleNamespace(role=role, parts=parts),
    ):
        with pytest.raises(SpeechTranscriptionError):
            await stt.transcribe(b"fake-audio-bytes")
