"""Structured logging configuration for the Agricultural AI platform.

Provides JSON-like structured log output with correlation-ID propagation so
that every log entry produced within the same request context can be traced
back to a single inbound call.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

correlation_id_ctx: ContextVar[str] = ContextVar(
    "correlation_id", default="no-correlation-id"
)


class StructuredFormatter(logging.Formatter):
    """Emit each log record as a structured, single-line JSON-like string."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        correlation_id = correlation_id_ctx.get()
        message = record.getMessage()

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            message = f"{message}\n{record.exc_text}"

        log_record = {
            "timestamp": timestamp,
            "level": record.levelname,
            "name": record.name,
            "correlation_id": correlation_id,
            "message": message,
        }
        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with structured formatting.

    Parameters
    ----------
    level:
        Logging level name (e.g. ``"DEBUG"``, ``"INFO"``).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Avoid duplicate handlers when called more than once
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Parameters
    ----------
    name:
        Dot-separated logger name (typically ``__name__``).
    """
    return logging.getLogger(name)
