"""Input validation helpers for the Agricultural AI platform.

Each validator either returns a sanitised/normalised value or raises
:class:`~app.utils.exceptions.InvalidInputError` with a descriptive message.
"""

from __future__ import annotations

import re

from fastapi import UploadFile

ALLOWED_IMAGE_TYPES: set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
ALLOWED_IMAGE_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10 MB

ALLOWED_AUDIO_TYPES: set[str] = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/webm",
}
ALLOWED_AUDIO_EXTENSIONS: set[str] = {"wav", "mp3", "ogg", "webm"}
MAX_AUDIO_SIZE: int = 25 * 1024 * 1024  # 25 MB

SUPPORTED_LANGUAGES: set[str] = {"ar", "en"}
DEFAULT_LANGUAGE: str = "ar"

MAX_QUERY_LENGTH: int = 1000

# Pattern to strip characters that are not alphanumeric, whitespace, or
# common Arabic / punctuation ranges.
_SANITIZE_RE = re.compile(r"[^\w\s\u0600-\u06FF.,;:!?()'\"-]", re.UNICODE)


async def validate_image(file: UploadFile) -> bool:
    """Validate that *file* is an acceptable image upload.

    Returns ``True`` on success; raises ``InvalidInputError`` otherwise.
    """
    from app.utils.exceptions import InvalidInputError

    if file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise InvalidInputError(
                message=f"Unsupported image extension '.{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
                error_code="INVALID_IMAGE_TYPE",
            )

    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise InvalidInputError(
            message=f"Unsupported image content type '{file.content_type}'.",
            error_code="INVALID_IMAGE_TYPE",
        )

    content = await file.read()
    await file.seek(0)  # reset for downstream consumers

    if len(content) > MAX_IMAGE_SIZE:
        raise InvalidInputError(
            message=f"Image exceeds maximum size of {MAX_IMAGE_SIZE // (1024 * 1024)} MB.",
            error_code="IMAGE_TOO_LARGE",
        )

    return True


async def validate_audio(file: UploadFile) -> bool:
    """Validate that *file* is an acceptable audio upload.

    Returns ``True`` on success; raises ``InvalidInputError`` otherwise.
    """
    from app.utils.exceptions import InvalidInputError

    if file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            raise InvalidInputError(
                message=f"Unsupported audio extension '.{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}",
                error_code="INVALID_AUDIO_TYPE",
            )

    if file.content_type and file.content_type not in ALLOWED_AUDIO_TYPES:
        raise InvalidInputError(
            message=f"Unsupported audio content type '{file.content_type}'.",
            error_code="INVALID_AUDIO_TYPE",
        )

    content = await file.read()
    await file.seek(0)

    if len(content) > MAX_AUDIO_SIZE:
        raise InvalidInputError(
            message=f"Audio exceeds maximum size of {MAX_AUDIO_SIZE // (1024 * 1024)} MB.",
            error_code="AUDIO_TOO_LARGE",
        )

    return True


def validate_language(lang: str) -> str:
    """Return a normalised language code.

    Falls back to :data:`DEFAULT_LANGUAGE` when *lang* is empty or
    unsupported.
    """
    lang = lang.strip().lower() if lang else DEFAULT_LANGUAGE
    if lang not in SUPPORTED_LANGUAGES:
        return DEFAULT_LANGUAGE
    return lang


def validate_query(query: str) -> str:
    """Sanitise and validate a user query string.

    Raises ``InvalidInputError`` when the query is empty or exceeds
    :data:`MAX_QUERY_LENGTH`.
    """
    from app.utils.exceptions import InvalidInputError

    if not query or not query.strip():
        raise InvalidInputError(
            message="Query must not be empty.",
            error_code="EMPTY_QUERY",
        )

    query = query.strip()

    if len(query) > MAX_QUERY_LENGTH:
        raise InvalidInputError(
            message=f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters.",
            error_code="QUERY_TOO_LONG",
        )

    query = _SANITIZE_RE.sub("", query)
    return query
