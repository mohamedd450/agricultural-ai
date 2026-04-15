"""Prometheus metrics and FastAPI middleware for the Agricultural AI platform.

Exposes standard RED (Rate, Errors, Duration) metrics plus domain-specific
counters for cache hits/misses and model inference time.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ── Metric definitions ───────────────────────────────────────────────────────

REQUEST_COUNT: Counter = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY: Histogram = Histogram(
    "api_request_duration_seconds",
    "Request latency",
    ["method", "endpoint"],
)

ACTIVE_CONNECTIONS: Gauge = Gauge(
    "api_active_connections",
    "Active connections",
)

MODEL_INFERENCE_TIME: Histogram = Histogram(
    "model_inference_seconds",
    "Model inference time",
    ["model_name"],
)

CACHE_HITS: Counter = Counter(
    "cache_hits_total",
    "Cache hits",
    ["cache_type"],
)

CACHE_MISSES: Counter = Counter(
    "cache_misses_total",
    "Cache misses",
    ["cache_type"],
)


# ── Middleware ────────────────────────────────────────────────────────────────


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record request count, latency, and active-connection metrics."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        ACTIVE_CONNECTIONS.inc()
        start = time.perf_counter()
        status = "500"

        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            raise
        finally:
            duration = time.perf_counter() - start
            ACTIVE_CONNECTIONS.dec()
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status,
            ).inc()


# ── Context-manager helper ───────────────────────────────────────────────────


@contextmanager
def track_time(histogram: Histogram, **labels: str) -> Generator[None, None, None]:
    """Context manager that records elapsed time to a Prometheus histogram.

    Usage::

        with track_time(MODEL_INFERENCE_TIME, model_name="efficientnet_b0"):
            result = model.predict(image)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        histogram.labels(**labels).observe(time.perf_counter() - start)
