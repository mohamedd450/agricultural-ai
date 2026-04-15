"""Voice processing service for Arabic and English speech.

Uses OpenAI Whisper for speech-to-text and gTTS for text-to-speech.
Both backends degrade gracefully when unavailable.
"""

import io
import logging
import os
import tempfile
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"ar", "en", "fr", "es", "de", "hi", "ur", "tr"}


def _try_load_whisper():
    """Attempt to import the Whisper speech-to-text library."""
    try:
        import whisper

        return whisper
    except ImportError:
        logger.warning("whisper not available – STT disabled")
        return None


def _try_load_gtts():
    """Attempt to import gTTS for text-to-speech."""
    try:
        from gtts import gTTS

        return gTTS
    except ImportError:
        logger.warning("gTTS not available – TTS disabled")
        return None


class VoiceService:
    """Voice processing service supporting Arabic and English.

    Handles speech-to-text transcription via Whisper and text-to-speech
    synthesis via gTTS, with graceful fallback when either dependency
    is missing.

    Args:
        whisper_model: Optional pre-loaded Whisper model for testing.
    """

    def __init__(self, whisper_model: Any = None) -> None:
        self._settings = get_settings()
        self._whisper = _try_load_whisper()
        self._gTTS = _try_load_gtts()
        self._model = whisper_model
        self._model_name: str = self._settings.whisper_model

        if self._whisper is not None and self._model is None:
            self._model = self._load_whisper_model()

        logger.info(
            "VoiceService initialised (STT=%s, TTS=%s)",
            "ready" if self._model is not None else "unavailable",
            "ready" if self._gTTS is not None else "unavailable",
        )

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_whisper_model(self) -> Any:
        """Load the configured Whisper model."""
        if self._whisper is None:
            return None
        try:
            model = self._whisper.load_model(self._model_name)
            logger.info("Whisper model '%s' loaded", self._model_name)
            return model
        except Exception:
            logger.exception("Failed to load Whisper model '%s'", self._model_name)
            return None

    # ------------------------------------------------------------------
    # Speech-to-text
    # ------------------------------------------------------------------

    async def speech_to_text(
        self, audio_data: bytes, language: str = "ar"
    ) -> str:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (WAV / MP3 / OGG / WebM).
            language: ISO 639-1 language code (default ``"ar"``).

        Returns:
            Transcribed text string, or an empty string on failure.
        """
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(
                "Unsupported language '%s' – falling back to 'en'", language
            )
            language = "en"

        logger.info(
            "STT request: %d bytes, language=%s", len(audio_data), language
        )

        if self._model is None:
            logger.warning("Whisper model unavailable – returning empty transcription")
            return ""

        temp_path: str | None = None
        try:
            # Whisper requires a file path, so write audio to a temp file
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp.write(audio_data)
                temp_path = tmp.name

            result = self._model.transcribe(
                temp_path,
                language=language,
                fp16=False,
            )
            text: str = result.get("text", "").strip()
            logger.info(
                "STT complete: %d chars transcribed (language=%s)",
                len(text),
                language,
            )
            return text

        except Exception:
            logger.exception("Speech-to-text failed")
            return ""
        finally:
            self._cleanup_temp(temp_path)

    # ------------------------------------------------------------------
    # Text-to-speech
    # ------------------------------------------------------------------

    async def text_to_speech(
        self, text: str, language: str = "ar"
    ) -> bytes:
        """Synthesise speech from text.

        Args:
            text: The text to convert to speech.
            language: ISO 639-1 language code (default ``"ar"``).

        Returns:
            MP3-encoded audio bytes, or empty bytes on failure.
        """
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(
                "Unsupported language '%s' – falling back to 'en'", language
            )
            language = "en"

        logger.info(
            "TTS request: %d chars, language=%s", len(text), language
        )

        if self._gTTS is None:
            logger.warning("gTTS unavailable – returning empty audio")
            return b""

        temp_path: str | None = None
        try:
            tts = self._gTTS(text=text, lang=language)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            audio_bytes = buf.getvalue()

            logger.info(
                "TTS complete: %d bytes generated (language=%s)",
                len(audio_bytes),
                language,
            )
            return audio_bytes

        except Exception:
            logger.exception("Text-to-speech failed")
            return b""
        finally:
            self._cleanup_temp(temp_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cleanup_temp(path: str | None) -> None:
        """Remove a temporary file if it exists."""
        if path is None:
            return
        try:
            if os.path.exists(path):
                os.unlink(path)
                logger.debug("Cleaned up temp file %s", path)
        except OSError:
            logger.warning("Failed to clean up temp file %s", path)
