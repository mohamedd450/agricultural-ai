"""Text cleaning and normalization for Arabic and English agricultural text.

Provides utilities for removing noise, normalizing Arabic characters,
and preparing text for downstream processing.
"""

from __future__ import annotations

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# Arabic diacritics range (tashkeel)
_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670]")

# Arabic punctuation and special characters to normalize
_ALEF_VARIANTS_RE = re.compile(r"[\u0622\u0623\u0625\u0671]")
_WAW_HAMZA_RE = re.compile(r"\u0624")
_YAA_HAMZA_RE = re.compile(r"\u0626")
_TAA_MARBUTA_RE = re.compile(r"\u0629")
_ALEF_MAQSURA_RE = re.compile(r"\u0649")

# Whitespace normalization
_WHITESPACE_RE = re.compile(r"\s+")

# URL pattern
_URL_RE = re.compile(r"https?://\S+|www\.\S+")

# Email pattern
_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")

# Repeated characters (e.g. "aaaaa" → "aa")
_REPEATED_CHARS_RE = re.compile(r"(.)\1{2,}")


class TextCleaner:
    """Clean and normalize agricultural text for NLP processing.

    Supports Arabic Unicode normalization and Latin text cleanup.

    Parameters
    ----------
    normalize_arabic:
        Apply Arabic character normalization (alef variants, tashkeel, etc.).
    remove_urls:
        Strip HTTP/HTTPS URLs from text.
    remove_emails:
        Strip email addresses from text.
    min_length:
        Minimum character length for a text to be considered non-empty
        after cleaning.
    """

    def __init__(
        self,
        normalize_arabic: bool = True,
        remove_urls: bool = True,
        remove_emails: bool = True,
        min_length: int = 10,
    ) -> None:
        self.normalize_arabic = normalize_arabic
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        self.min_length = min_length

    # ── Public API ────────────────────────────────────────────────────────

    def clean(self, text: str) -> str:
        """Apply the full cleaning pipeline to *text*.

        Steps
        -----
        1. Unicode normalization (NFC)
        2. Remove URLs and emails (if enabled)
        3. Arabic-specific normalization (if enabled)
        4. Collapse whitespace

        Parameters
        ----------
        text:
            Raw input text.

        Returns
        -------
        str
            Cleaned text, or an empty string if below *min_length*.
        """
        if not text:
            return ""

        # 1. NFC normalization preserves Arabic composed forms
        text = unicodedata.normalize("NFC", text)

        # 2. Remove noise
        if self.remove_urls:
            text = _URL_RE.sub(" ", text)
        if self.remove_emails:
            text = _EMAIL_RE.sub(" ", text)

        # 3. Arabic normalization
        if self.normalize_arabic:
            text = self._normalize_arabic(text)

        # 4. Whitespace
        text = _WHITESPACE_RE.sub(" ", text).strip()

        if len(text) < self.min_length:
            return ""

        return text

    def clean_batch(self, texts: list[str]) -> list[str]:
        """Clean a list of texts, discarding those that become empty.

        Parameters
        ----------
        texts:
            List of raw input strings.

        Returns
        -------
        list[str]
            List of cleaned, non-empty strings.
        """
        cleaned = [self.clean(t) for t in texts]
        return [t for t in cleaned if t]

    def is_arabic(self, text: str) -> bool:
        """Return ``True`` if the majority of characters are Arabic.

        Parameters
        ----------
        text:
            Input string to check.
        """
        if not text:
            return False
        arabic_chars = sum(
            1 for ch in text if "\u0600" <= ch <= "\u06FF"
        )
        return arabic_chars / max(len(text), 1) > 0.3

    def detect_language(self, text: str) -> str:
        """Heuristically detect the language of *text*.

        Returns ``"ar"`` for Arabic-majority text, ``"en"`` otherwise.
        """
        return "ar" if self.is_arabic(text) else "en"

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _normalize_arabic(text: str) -> str:
        """Apply Arabic-specific character normalizations.

        - Remove diacritics (tashkeel / harakat)
        - Unify alef variants → plain alef (ا)
        - Normalize waw with hamza (ؤ → و)
        - Normalize yaa with hamza (ئ → ي)
        - Convert taa marbuta (ة → ه)
        - Convert alef maqsura (ى → ي)
        """
        # Remove diacritics
        text = _DIACRITICS_RE.sub("", text)

        # Unify alef variants: آ أ إ ٱ → ا
        text = _ALEF_VARIANTS_RE.sub("\u0627", text)

        # ؤ → و
        text = _WAW_HAMZA_RE.sub("\u0648", text)

        # ئ → ي
        text = _YAA_HAMZA_RE.sub("\u064A", text)

        # ة → ه
        text = _TAA_MARBUTA_RE.sub("\u0647", text)

        # ى → ي
        text = _ALEF_MAQSURA_RE.sub("\u064A", text)

        return text
