"""Tests for VoiceService."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.voice_service import SUPPORTED_LANGUAGES, VoiceService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def _mock_settings():
    settings = MagicMock(whisper_model="base")
    with patch("app.services.voice_service.get_settings", return_value=settings):
        yield settings


@pytest.fixture
def voice_service(_mock_settings):
    """VoiceService with mocked whisper and gTTS."""
    mock_whisper_model = MagicMock()
    mock_whisper_model.transcribe.return_value = {"text": "sample transcription"}

    mock_gtts_cls = MagicMock()
    mock_gtts_instance = MagicMock()
    mock_gtts_instance.write_to_fp.side_effect = lambda fp: fp.write(b"audio-bytes-here")
    mock_gtts_cls.return_value = mock_gtts_instance

    with (
        patch("app.services.voice_service._try_load_whisper", return_value=MagicMock()),
        patch("app.services.voice_service._try_load_gtts", return_value=mock_gtts_cls),
    ):
        svc = VoiceService(whisper_model=mock_whisper_model)
        svc._gTTS = mock_gtts_cls
        return svc


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_text_to_speech_returns_bytes(voice_service):
    """TTS should return non-empty bytes."""
    audio = await voice_service.text_to_speech("Hello farmer", language="en")
    assert isinstance(audio, bytes)
    assert len(audio) > 0


@pytest.mark.asyncio
async def test_speech_to_text_with_mock(voice_service):
    """STT should return the mocked transcription text."""
    text = await voice_service.speech_to_text(b"fake-audio", language="ar")
    assert isinstance(text, str)
    assert text == "sample transcription"


def test_language_support():
    """Verify supported language codes."""
    assert "ar" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    assert "fr" in SUPPORTED_LANGUAGES
    assert len(SUPPORTED_LANGUAGES) >= 8
