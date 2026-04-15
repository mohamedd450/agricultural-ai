"""Text cleaning utilities for agricultural document processing."""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


class TextCleaner:
    """Cleans and normalizes extracted text from documents."""

    def clean(self, text: str) -> str:
        """Run the full cleaning pipeline on input text.

        Args:
            text: Raw input text.

        Returns:
            Cleaned text.
        """
        if not text:
            return ""

        text = self.fix_encoding(text)
        text = self.remove_headers_footers(text)
        text = self.normalize_arabic(text)
        text = self.remove_special_characters(text)
        text = self._normalize_whitespace(text)
        return text.strip()

    def remove_headers_footers(self, text: str) -> str:
        """Remove common header and footer patterns.

        Args:
            text: Input text.

        Returns:
            Text with headers/footers removed.
        """
        lines = text.split("\n")
        if len(lines) <= 4:
            return text

        cleaned_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            # Skip page numbers
            if re.match(r"^[\d\s\-–—]+$", stripped):
                continue
            # Skip common header/footer patterns
            if re.match(r"^(page|صفحة)\s*\d+", stripped, re.IGNORECASE):
                continue
            if re.match(r"^\d+\s*of\s*\d+$", stripped, re.IGNORECASE):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def normalize_arabic(self, text: str) -> str:
        """Normalize Arabic characters for consistency.

        Normalizes various forms of alef, teh marbuta, and diacritics.

        Args:
            text: Input text with Arabic content.

        Returns:
            Text with normalized Arabic characters.
        """
        # Normalize alef variants to plain alef
        text = re.sub(r"[\u0622\u0623\u0625]", "\u0627", text)
        # Normalize teh marbuta to heh
        text = text.replace("\u0629", "\u0647")
        # Remove Arabic diacritics (tashkeel)
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        # Normalize Unicode
        text = unicodedata.normalize("NFC", text)
        return text

    def remove_special_characters(self, text: str) -> str:
        """Remove special characters while preserving Arabic and Latin text.

        Args:
            text: Input text.

        Returns:
            Text with special characters removed.
        """
        # Keep Arabic, Latin, digits, basic punctuation, and whitespace
        text = re.sub(
            r"[^\u0600-\u06FF\u0750-\u077Fa-zA-Z0-9\s.,;:!?()\"'\-/\n]",
            " ",
            text,
        )
        return text

    def fix_encoding(self, text: str) -> str:
        """Fix common encoding issues.

        Args:
            text: Input text with potential encoding problems.

        Returns:
            Text with fixed encoding.
        """
        try:
            if isinstance(text, bytes):
                text = text.decode("utf-8", errors="replace")
            # Replace common mojibake patterns
            text = text.replace("\ufffd", " ")
            text = text.replace("\x00", "")
            text = unicodedata.normalize("NFC", text)
        except Exception as e:
            logger.warning("Encoding fix failed: %s", e)
        return text

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text.

        Args:
            text: Input text.

        Returns:
            Text with normalized whitespace.
        """
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text
