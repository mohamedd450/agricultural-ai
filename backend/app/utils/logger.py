"""Structured logging setup for the Agricultural AI Platform."""

import logging
import json
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFilter(logging.Filter):
    """Inject the current request ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("")  # type: ignore[attr-defined]
        return True


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects (production)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        req_id = getattr(record, "request_id", "")
        if req_id:
            log_entry["request_id"] = req_id

        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-friendly coloured formatter for local development."""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[1;31m",  # bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        req_id = getattr(record, "request_id", "")
        prefix = f"[{req_id}] " if req_id else ""
        return (
            f"{color}{record.levelname:<8}{self.RESET} "
            f"{prefix}{record.name}: {record.getMessage()}"
        )


def setup_logging(level: str = "INFO", *, json_output: bool = False) -> None:
    """Configure the root logger for the application.

    Parameters
    ----------
    level:
        Logging level name (``DEBUG``, ``INFO``, ``WARNING``, …).
    json_output:
        When *True*, use :class:`JSONFormatter` (production).
        When *False*, use :class:`ConsoleFormatter` (development).
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove any pre-existing handlers to avoid duplicates on re-init
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIDFilter())

    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root.addHandler(handler)

    # Quieten noisy third-party loggers
    for name in ("uvicorn.access", "httpcore", "httpx", "neo4j"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with the request-ID filter attached."""
    logger = logging.getLogger(name)
    if not any(isinstance(f, RequestIDFilter) for f in logger.filters):
        logger.addFilter(RequestIDFilter())
    return logger
