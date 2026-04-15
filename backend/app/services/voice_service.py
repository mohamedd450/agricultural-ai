"""Voice service for speech-to-text and text-to-speech operations."""

from __future__ import annotations

import io
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import whisper  # type: ignore[import-untyped]

    WHISPER_AVAILABLE = True
except ImportError:  # pragma: no cover
    WHISPER_AVAILABLE = False
    logger.warning(
        "openai-whisper not installed – speech-to-text will be unavailable"
    )

try:
    from gtts import gTTS  # type: ignore[import-untyped]

    GTTS_AVAILABLE = True
except ImportError:  # pragma: no cover
    GTTS_AVAILABLE = False
    logger.warning("gTTS not installed – text-to-speech will be unavailable")


class VoiceService:
    """Bidirectional voice ↔ text service for the agricultural AI platform."""

    def __init__(self, whisper_model_size: str = "base") -> None:
        self.whisper_model_size = whisper_model_size
        self.whisper_model: Optional[object] = None

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    async def load_model(self) -> None:
        """Load the Whisper speech-recognition model."""
        if not WHISPER_AVAILABLE:
            logger.warning(
                "Whisper is not installed – skipping model load"
            )
            return

        try:
            self.whisper_model = whisper.load_model(self.whisper_model_size)
            logger.info(
                "Whisper '%s' model loaded successfully",
                self.whisper_model_size,
            )
        except Exception:
            logger.error(
                "Failed to load Whisper '%s' model",
                self.whisper_model_size,
                exc_info=True,
            )
            self.whisper_model = None

    # ------------------------------------------------------------------
    # Speech-to-text
    # ------------------------------------------------------------------

    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str = "ar",
    ) -> dict:
        """Transcribe raw audio bytes to text.

        Returns
        -------
        dict
            ``{"text": str, "language": str, "confidence": float}``
        """
        if self.whisper_model is None:
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "error": "Whisper model not loaded",
            }

        try:
            import os
            import tempfile

            # Whisper requires a file path – use a secure temp file
            fd, tmp_path = tempfile.mkstemp(suffix=".wav")
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(audio_data)

                result = self.whisper_model.transcribe(  # type: ignore[union-attr]
                    tmp_path,
                    language=language,
                )
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            segments = result.get("segments", [])
            avg_confidence = 0.0
            if segments:
                avg_confidence = sum(
                    seg.get("avg_logprob", 0.0) for seg in segments
                ) / len(segments)
                # Convert log-prob to a 0-1 confidence estimate
                import math

                avg_confidence = round(
                    min(1.0, max(0.0, math.exp(avg_confidence))), 4
                )

            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language", language),
                "confidence": avg_confidence,
            }
        except Exception:
            logger.error("Speech-to-text transcription failed", exc_info=True)
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "error": "Transcription failed",
            }

    # ------------------------------------------------------------------
    # Text-to-speech
    # ------------------------------------------------------------------

    async def text_to_speech(
        self,
        text: str,
        language: str = "ar",
    ) -> bytes:
        """Convert *text* to spoken audio bytes (MP3).

        Returns an empty ``bytes`` object on failure.
        """
        if not GTTS_AVAILABLE:
            logger.warning("gTTS unavailable – cannot synthesise speech")
            return b""

        try:
            tts = gTTS(text=text, lang=language)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            logger.info(
                "Text-to-speech generated %d bytes for language '%s'",
                buffer.getbuffer().nbytes,
                language,
            )
            return buffer.getvalue()
        except Exception:
            logger.error("Text-to-speech synthesis failed", exc_info=True)
            return b""

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` when the Whisper model is ready."""
        return self.whisper_model is not None
