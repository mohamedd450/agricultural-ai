"""Input validation helpers for the Agricultural AI Platform."""

from __future__ import annotations

import re
from typing import Final

# ---------- image validation ----------

VALID_IMAGE_HEADERS: Final[list[bytes]] = [
    b"\xff\xd8\xff",        # JPEG / JFIF
    b"\x89PNG\r\n\x1a\n",   # PNG
    b"RIFF",                 # WebP (begins with RIFF)
]

MAX_IMAGE_SIZE: Final[int] = 10 * 1024 * 1024   # 10 MB
MAX_AUDIO_SIZE: Final[int] = 50 * 1024 * 1024   # 50 MB
SUPPORTED_LANGUAGES: Final[frozenset[str]] = frozenset({"en", "ar"})


def validate_image(data: bytes) -> bool:
    """Return *True* when *data* looks like a supported image within size limits."""
    if not data or len(data) > MAX_IMAGE_SIZE:
        return False
    return any(data[:len(header)] == header for header in VALID_IMAGE_HEADERS)


# ---------- audio validation ----------

VALID_AUDIO_HEADERS: Final[list[bytes]] = [
    b"RIFF",          # WAV
    b"\xff\xfb",      # MP3 (MPEG frame sync)
    b"\xff\xf3",      # MP3 variant
    b"\xff\xf2",      # MP3 variant
    b"ID3",           # MP3 with ID3 tag
    b"OggS",          # OGG / Opus
    b"fLaC",          # FLAC
]


def validate_audio(data: bytes) -> bool:
    """Return *True* when *data* looks like a supported audio file within size limits."""
    if not data or len(data) > MAX_AUDIO_SIZE:
        return False
    return any(data[:len(header)] == header for header in VALID_AUDIO_HEADERS)


# ---------- language validation ----------


def validate_language(lang: str) -> str:
    """Normalise and validate a language code.

    Returns the canonical lower-case code or raises :class:`ValueError`.
    """
    normalised = lang.strip().lower()[:2]
    if normalised not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{lang}'. Must be one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
        )
    return normalised


# ---------- text sanitisation ----------

# Characters / patterns that should never appear in user queries.
_DANGEROUS_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*/\s*script[^>]*>", re.IGNORECASE),  # stray closing script tags
    re.compile(r"<[^>]+>"),                          # HTML tags
    re.compile(
        r"\b(?:DROP\s+TABLE|DELETE\s+FROM|TRUNCATE\s+TABLE|ALTER\s+TABLE)\b",
        re.IGNORECASE,
    ),
]

# Prompt-injection guard – strip common system/role override attempts.
_INJECTION_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(
        r"(ignore\s+(all\s+)?previous\s+instructions)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(you\s+are\s+now|act\s+as\s+if|pretend\s+(to\s+be|you\s+are))",
        re.IGNORECASE,
    ),
    re.compile(
        r"(system\s*:\s*|###\s*system\s*prompt)",
        re.IGNORECASE,
    ),
]


def sanitize_text(text: str) -> str:
    """Remove dangerous characters and prompt-injection attempts from *text*."""
    cleaned = text

    for pattern in _DANGEROUS_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    for pattern in _INJECTION_PATTERNS:
        cleaned = pattern.sub("[FILTERED]", cleaned)

    # Collapse excessive whitespace
    cleaned = re.sub(r"\s{3,}", "  ", cleaned).strip()
    return cleaned


# ---------- query length validation ----------


def validate_query_length(query: str, max_len: int = 1000) -> bool:
    """Return *True* when *query* is non-empty and within *max_len* characters."""
    return 0 < len(query.strip()) <= max_len
