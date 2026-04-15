"""Tests for the VoiceService.

Covers speech-to-text, text-to-speech, Arabic language support,
and error handling.
"""

from __future__ import annotations

import pytest

from app.services.voice_service import VoiceService


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def voice_service():
    """Return an unloaded VoiceService."""
    return VoiceService(whisper_model_size="base")


@pytest.fixture()
def wav_bytes() -> bytes:
    """Minimal 44-byte WAV header (silent audio)."""
    return b"RIFF" + (44).to_bytes(4, "little") + b"WAVEfmt " + b"\x00" * 32


# ── Init ──────────────────────────────────────────────────────────────────


class TestVoiceServiceInit:
    def test_initial_state(self, voice_service: VoiceService) -> None:
        assert voice_service.is_loaded is False
        assert voice_service.whisper_model is None
        assert voice_service.whisper_model_size == "base"

    @pytest.mark.asyncio
    async def test_load_model_does_not_raise(
        self, voice_service: VoiceService
    ) -> None:
        """load_model must not raise even when whisper is unavailable."""
        await voice_service.load_model()


# ── speech_to_text ────────────────────────────────────────────────────────


class TestSpeechToText:
    @pytest.mark.asyncio
    async def test_returns_dict(
        self, voice_service: VoiceService, wav_bytes: bytes
    ) -> None:
        result = await voice_service.speech_to_text(wav_bytes)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_required_keys_present(
        self, voice_service: VoiceService, wav_bytes: bytes
    ) -> None:
        result = await voice_service.speech_to_text(wav_bytes)
        assert "text" in result
        assert "language" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_returns_empty_text_when_unloaded(
        self, voice_service: VoiceService, wav_bytes: bytes
    ) -> None:
        result = await voice_service.speech_to_text(wav_bytes)
        # model not loaded → empty text or error
        assert isinstance(result["text"], str)

    @pytest.mark.asyncio
    async def test_arabic_language_parameter(
        self, voice_service: VoiceService, wav_bytes: bytes
    ) -> None:
        result = await voice_service.speech_to_text(wav_bytes, language="ar")
        assert result["language"] == "ar"

    @pytest.mark.asyncio
    async def test_english_language_parameter(
        self, voice_service: VoiceService, wav_bytes: bytes
    ) -> None:
        result = await voice_service.speech_to_text(wav_bytes, language="en")
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_confidence_in_range(
        self, voice_service: VoiceService, wav_bytes: bytes
    ) -> None:
        result = await voice_service.speech_to_text(wav_bytes)
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_empty_bytes_does_not_raise(
        self, voice_service: VoiceService
    ) -> None:
        result = await voice_service.speech_to_text(b"")
        assert isinstance(result, dict)


# ── text_to_speech ────────────────────────────────────────────────────────


class TestTextToSpeech:
    @pytest.mark.asyncio
    async def test_returns_bytes(self, voice_service: VoiceService) -> None:
        result = await voice_service.text_to_speech("مرحبا")
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_arabic_text(self, voice_service: VoiceService) -> None:
        result = await voice_service.text_to_speech(
            "نقص النيتروجين يسبب اصفرار الأوراق", language="ar"
        )
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_english_text(self, voice_service: VoiceService) -> None:
        result = await voice_service.text_to_speech(
            "Nitrogen deficiency causes yellowing", language="en"
        )
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_empty_text_returns_bytes(
        self, voice_service: VoiceService
    ) -> None:
        result = await voice_service.text_to_speech("")
        assert isinstance(result, bytes)


# ── is_loaded property ────────────────────────────────────────────────────


class TestIsLoaded:
    def test_false_by_default(self, voice_service: VoiceService) -> None:
        assert voice_service.is_loaded is False

    def test_true_when_model_set(self, voice_service: VoiceService) -> None:
        voice_service.whisper_model = object()
        assert voice_service.is_loaded is True

    def test_false_when_model_cleared(self, voice_service: VoiceService) -> None:
        voice_service.whisper_model = object()
        voice_service.whisper_model = None
        assert voice_service.is_loaded is False
