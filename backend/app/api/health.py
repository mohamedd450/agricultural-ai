"""Health, readiness, and liveness probe endpoints.

These routes are designed for container orchestrators (Kubernetes, ECS, etc.)
and load-balancer health checks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import (
    get_cache_service,
    get_graph_rag_service,
    get_neo4j_client,
    get_vector_db_service,
    get_vision_service,
    get_voice_service,
)
from app.database.neo4j_client import Neo4jClient
from app.models.response_models import HealthResponse
from app.services.cache_service import CacheService
from app.services.graph_rag_service import GraphRAGService
from app.services.vector_db_service import VectorDBService
from app.services.vision_service import VisionService
from app.services.voice_service import VoiceService
from app.utils.logger import get_logger

logger: logging.Logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


def _service_status(available: bool) -> str:
    """Return ``'healthy'`` or ``'degraded'`` based on a boolean flag."""
    return "healthy" if available else "degraded"


# ── GET / ────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Full health check",
    description=(
        "Returns the operational status of every backend service.  An overall "
        "status of ``'healthy'`` means all subsystems are operational; "
        "``'degraded'`` means at least one subsystem is unavailable."
    ),
)
async def health_check(
    vision: VisionService = Depends(get_vision_service),
    voice: VoiceService = Depends(get_voice_service),
    graph_rag: GraphRAGService = Depends(get_graph_rag_service),
    vector_db: VectorDBService = Depends(get_vector_db_service),
    cache: CacheService = Depends(get_cache_service),
    neo4j: Neo4jClient = Depends(get_neo4j_client),
) -> HealthResponse:
    services: dict[str, str] = {
        "vision": _service_status(vision.is_loaded),
        "voice": _service_status(voice.is_loaded),
        "graph_rag": _service_status(graph_rag.is_available),
        "vector_db": _service_status(vector_db.is_available),
        "cache": _service_status(cache.is_connected),
        "neo4j": _service_status(neo4j.is_connected),
    }

    all_healthy = all(v == "healthy" for v in services.values())
    overall = "healthy" if all_healthy else "degraded"

    logger.debug("Health check: %s – %s", overall, services)

    return HealthResponse(
        status=overall,
        services=services,
        timestamp=datetime.now(timezone.utc),
    )


# ── GET /ready ───────────────────────────────────────────────────────────────


@router.get(
    "/ready",
    summary="Readiness probe",
    description=(
        "Returns HTTP 200 when the minimum set of core services (graph-RAG "
        "and vector DB) are available.  Returns HTTP 503 otherwise."
    ),
)
async def readiness(
    response: Response,
    graph_rag: GraphRAGService = Depends(get_graph_rag_service),
    vector_db: VectorDBService = Depends(get_vector_db_service),
) -> dict[str, str]:
    core_ready = graph_rag.is_available and vector_db.is_available

    if not core_ready:
        logger.warning("Readiness check failed: graph_rag=%s vector_db=%s", graph_rag.is_available, vector_db.is_available)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}

    return {"status": "ready"}


# ── GET /live ────────────────────────────────────────────────────────────────


@router.get(
    "/live",
    summary="Liveness probe",
    description="Always returns HTTP 200 to confirm the process is running.",
)
async def liveness() -> dict[str, str]:
    return {"status": "alive"}
