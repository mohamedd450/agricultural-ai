"""Prometheus-compatible metrics and FastAPI middleware."""

from __future__ import annotations

import time
from typing import Callable

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Try to import the official Prometheus client; fall back to lightweight stubs
# so that the rest of the application still works without it installed.
# ---------------------------------------------------------------------------
try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )

    REGISTRY = CollectorRegistry()

    REQUEST_COUNT = Counter(
        "agri_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
        registry=REGISTRY,
    )

    REQUEST_LATENCY = Histogram(
        "agri_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["endpoint"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=REGISTRY,
    )

    ACTIVE_CONNECTIONS = Gauge(
        "agri_active_connections",
        "Currently active connections",
        registry=REGISTRY,
    )

    SERVICE_ERRORS = Counter(
        "agri_service_errors_total",
        "Errors from downstream services",
        ["service_name"],
        registry=REGISTRY,
    )

    CACHE_HITS = Counter(
        "agri_cache_hits_total",
        "Cache hit count",
        registry=REGISTRY,
    )

    CACHE_MISSES = Counter(
        "agri_cache_misses_total",
        "Cache miss count",
        registry=REGISTRY,
    )

    _PROMETHEUS_AVAILABLE = True
    logger.debug("prometheus_client loaded – real metrics enabled")

except ImportError:  # pragma: no cover – stub fallback

    class _Noop:
        """Minimal stub that silently accepts any metric call."""

        def labels(self, *_a, **_kw):  # type: ignore[override]
            return self

        def inc(self, amount: float = 1) -> None: ...
        def dec(self, amount: float = 1) -> None: ...
        def observe(self, amount: float) -> None: ...
        def set(self, value: float) -> None: ...

    REQUEST_COUNT = _Noop()  # type: ignore[assignment]
    REQUEST_LATENCY = _Noop()  # type: ignore[assignment]
    ACTIVE_CONNECTIONS = _Noop()  # type: ignore[assignment]
    SERVICE_ERRORS = _Noop()  # type: ignore[assignment]
    CACHE_HITS = _Noop()  # type: ignore[assignment]
    CACHE_MISSES = _Noop()  # type: ignore[assignment]

    REGISTRY = None  # type: ignore[assignment]
    CONTENT_TYPE_LATEST = "text/plain; charset=utf-8"  # type: ignore[assignment]
    _PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not installed – metrics are no-ops")


# ---------------------------------------------------------------------------
# FastAPI middleware
# ---------------------------------------------------------------------------

class MetricsMiddleware:
    """ASGI middleware that records request count and latency.

    Usage::

        from app.utils.metrics import MetricsMiddleware
        app.add_middleware(MetricsMiddleware)
    """

    def __init__(self, app) -> None:  # noqa: ANN001 – ASGI app
        self.app = app

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        method: str = scope.get("method", "")
        status_code = 500  # default; overwritten on success

        ACTIVE_CONNECTIONS.inc()
        start = time.perf_counter()

        async def _send_wrapper(message) -> None:  # noqa: ANN001
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, _send_wrapper)
        finally:
            elapsed = time.perf_counter() - start
            REQUEST_COUNT.labels(
                method=method, endpoint=path, status=str(status_code)
            ).inc()
            REQUEST_LATENCY.labels(endpoint=path).observe(elapsed)
            ACTIVE_CONNECTIONS.dec()


# ---------------------------------------------------------------------------
# /metrics endpoint handler
# ---------------------------------------------------------------------------

async def metrics_endpoint():
    """Return Prometheus exposition-format metrics.

    Register this with your FastAPI router::

        from app.utils.metrics import metrics_endpoint
        router.add_api_route("/metrics", metrics_endpoint)
    """
    if not _PROMETHEUS_AVAILABLE or REGISTRY is None:
        from starlette.responses import PlainTextResponse

        return PlainTextResponse(
            "# prometheus_client not installed\n", status_code=200
        )

    from starlette.responses import Response

    body: bytes = generate_latest(REGISTRY)
    return Response(content=body, media_type=CONTENT_TYPE_LATEST)
