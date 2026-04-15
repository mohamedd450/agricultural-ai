"""FastAPI application entry point for the Agricultural AI platform."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.routes import router as api_router
from app.api.websocket import router as ws_router
from app.config import get_settings
from app.dependencies import (
    get_cache_service,
    get_graph_rag_service,
    get_neo4j_client,
    get_vector_db_service,
    get_vision_service,
    get_voice_service,
)
from app.security import RateLimitMiddleware
from app.utils.exceptions import (
    AgriPlatformError,
    agri_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)
from app.utils.logger import get_logger, setup_logging

logger: logging.Logger = get_logger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # ── Startup ──────────────────────────────────────────────────────────
    setup_logging(level=settings.log_level)
    logger.info("Starting %s v%s", settings.app_name, "1.0.0")

    # Cache
    cache = get_cache_service()
    try:
        await cache.connect()
    except Exception:
        logger.warning("Cache connection failed – continuing without cache", exc_info=True)

    # Neo4j
    neo4j = get_neo4j_client()
    try:
        await neo4j.connect()
    except Exception:
        logger.warning("Neo4j connection failed – continuing without graph DB", exc_info=True)

    # Vector DB
    vector_db = get_vector_db_service()
    try:
        await vector_db.initialize()
    except Exception:
        logger.warning("Vector DB init failed – continuing without vector search", exc_info=True)

    # Graph-RAG
    graph_rag = get_graph_rag_service()
    try:
        await graph_rag.initialize()
    except Exception:
        logger.warning("Graph-RAG init failed – continuing without graph RAG", exc_info=True)

    # Vision
    vision = get_vision_service()
    try:
        await vision.load_model()
    except Exception:
        logger.warning("Vision model load failed – continuing without vision", exc_info=True)

    # Voice
    voice = get_voice_service()
    try:
        await voice.load_model()
    except Exception:
        logger.warning("Voice model load failed – continuing without voice", exc_info=True)

    logger.info("All services initialised")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down – closing connections")

    try:
        await cache.disconnect()
    except Exception:
        logger.error("Error disconnecting cache", exc_info=True)

    try:
        await neo4j.close()
    except Exception:
        logger.error("Error closing Neo4j", exc_info=True)

    try:
        await vector_db.close()
    except Exception:
        logger.error("Error closing Vector DB", exc_info=True)

    try:
        await graph_rag.close()
    except Exception:
        logger.error("Error closing Graph-RAG", exc_info=True)

    logger.info("Shutdown complete")


# ── Application factory ──────────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title="Agricultural AI Platform",
    description=(
        "Multi-modal agricultural diagnostic platform combining computer "
        "vision, knowledge graphs, vector search, and voice interfaces "
        "to help farmers identify crop diseases and recommend treatments."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiting ────────────────────────────────────────────────────────────

app.add_middleware(RateLimitMiddleware)

# ── Metrics middleware ───────────────────────────────────────────────────────

if settings.prometheus_enabled:
    try:
        from app.utils.metrics import MetricsMiddleware

        app.add_middleware(MetricsMiddleware)
        logger.info("Prometheus MetricsMiddleware enabled")
    except Exception:
        logger.warning("Failed to enable MetricsMiddleware", exc_info=True)

# ── Exception handlers ───────────────────────────────────────────────────────

app.add_exception_handler(AgriPlatformError, agri_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, general_exception_handler)  # type: ignore[arg-type]

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(api_router)
app.include_router(health_router)
app.include_router(ws_router)

# ── Prometheus metrics endpoint ──────────────────────────────────────────────

if settings.prometheus_enabled:
    try:
        from prometheus_client import make_asgi_app

        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        logger.info("Prometheus metrics endpoint mounted at /metrics")
    except ImportError:
        logger.warning("prometheus_client not installed – /metrics endpoint unavailable")

# ── Static files for audio responses ─────────────────────────────────────────

_audio_dir = os.path.join(os.path.dirname(__file__), "static", "audio")
if os.path.isdir(_audio_dir):
    app.mount("/static/audio", StaticFiles(directory=_audio_dir), name="audio")
    logger.info("Serving audio static files from %s", _audio_dir)


# ── Root endpoint ────────────────────────────────────────────────────────────


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Return a welcome message."""
    return {
        "message": "Welcome to the Agricultural AI Platform",
        "version": "1.0.0",
        "docs": "/docs",
    }
