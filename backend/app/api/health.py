"""Health-check endpoints.

Provides liveness, readiness, and overall health status used by
orchestrators (Kubernetes, Docker Compose, etc.) and monitoring tools.
"""

import time
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app import __version__
from app.config import get_settings
from app.dependencies import get_neo4j_driver, get_qdrant_client, get_redis_client

router = APIRouter(prefix="/health", tags=["health"])

_START_TIME = time.time()


def _uptime() -> float:
    """Return process uptime in seconds."""
    return round(time.time() - _START_TIME, 2)


# ---------------------------------------------------------------------------
# GET /health — overall health summary
# ---------------------------------------------------------------------------
@router.get("", summary="Overall health check")
async def health() -> Dict[str, Any]:
    """Return overall platform health with version and uptime."""
    return {
        "status": "healthy",
        "version": __version__,
        "uptime_seconds": _uptime(),
    }


# ---------------------------------------------------------------------------
# GET /health/live — liveness probe
# ---------------------------------------------------------------------------
@router.get("/live", summary="Liveness probe")
async def liveness() -> Dict[str, str]:
    """Lightweight liveness check — the process is running."""
    return {"status": "alive"}


# ---------------------------------------------------------------------------
# GET /health/ready — readiness probe
# ---------------------------------------------------------------------------
@router.get("/ready", summary="Readiness probe")
async def readiness(
    redis=Depends(get_redis_client),
    neo4j=Depends(get_neo4j_driver),
    qdrant=Depends(get_qdrant_client),
) -> Dict[str, Any]:
    """Check connectivity to backing services and report readiness.

    Returns an HTTP 200 even when individual services are down so that
    the caller can inspect the ``services`` map and decide.
    """
    settings = get_settings()
    services: Dict[str, str] = {
        "redis": "connected" if redis is not None else "unavailable",
        "neo4j": "connected" if neo4j is not None else "unavailable",
        "qdrant": "connected" if qdrant is not None else "unavailable",
    }
    all_ready = all(v == "connected" for v in services.values())
    return {
        "status": "ready" if all_ready else "degraded",
        "version": settings.app_version,
        "uptime_seconds": _uptime(),
        "services": services,
    }
