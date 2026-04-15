"""Custom exception hierarchy and FastAPI exception handlers.

All domain-specific errors inherit from :class:`AgriPlatformError` so that a
single handler can capture every known failure and return a uniform JSON
envelope to the client.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Base exception ───────────────────────────────────────────────────────────


class AgriPlatformError(Exception):
    """Base exception for every application-level error."""

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        error_code: str = "PLATFORM_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


# ── Concrete exceptions ─────────────────────────────────────────────────────


class ServiceUnavailableError(AgriPlatformError):
    """A downstream service or dependency is unreachable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable.",
        error_code: str = "SERVICE_UNAVAILABLE",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            details=details,
        )


class ModelLoadError(AgriPlatformError):
    """An ML model failed to load or initialise."""

    def __init__(
        self,
        message: str = "Failed to load model.",
        error_code: str = "MODEL_LOAD_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            details=details,
        )


class InvalidInputError(AgriPlatformError):
    """The client supplied invalid or malformed input."""

    def __init__(
        self,
        message: str = "Invalid input provided.",
        error_code: str = "INVALID_INPUT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details,
        )


class AuthenticationError(AgriPlatformError):
    """Authentication or authorisation failure."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        error_code: str = "AUTHENTICATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
        )


class RateLimitError(AgriPlatformError):
    """The client has exceeded the allowed request rate."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=429,
            details=details,
        )


class GraphQueryError(AgriPlatformError):
    """A Neo4j / knowledge-graph query failed."""

    def __init__(
        self,
        message: str = "Graph query failed.",
        error_code: str = "GRAPH_QUERY_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=502,
            details=details,
        )


class VectorSearchError(AgriPlatformError):
    """A Qdrant / vector-search operation failed."""

    def __init__(
        self,
        message: str = "Vector search failed.",
        error_code: str = "VECTOR_SEARCH_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=502,
            details=details,
        )


class CacheError(AgriPlatformError):
    """A Redis / cache operation failed."""

    def __init__(
        self,
        message: str = "Cache operation failed.",
        error_code: str = "CACHE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=502,
            details=details,
        )


# ── Error-response envelope ─────────────────────────────────────────────────


def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {},
            }
        },
    )


# ── FastAPI exception handlers ──────────────────────────────────────────────


async def agri_exception_handler(
    request: Request,
    exc: AgriPlatformError,
) -> JSONResponse:
    """Handle all :class:`AgriPlatformError` subclasses."""
    logger.error(
        "AgriPlatformError: %s | code=%s status=%s path=%s",
        exc.message,
        exc.error_code,
        exc.status_code,
        request.url.path,
    )
    return _error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic / FastAPI request-validation errors."""
    logger.warning(
        "Validation error: %s path=%s",
        exc.errors(),
        request.url.path,
    )
    return _error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed.",
        details={"errors": exc.errors()},
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for unexpected exceptions."""
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )
    return _error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An unexpected internal error occurred.",
    )
