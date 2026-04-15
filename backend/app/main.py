"""FastAPI application entry point for the Agricultural AI Platform.

Creates the ASGI app, registers middleware, routers, event hooks, and
exception handlers.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import health, routes, websocket
from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple Prometheus-style metrics (in-memory counters)
# ---------------------------------------------------------------------------
_metrics: Dict[str, Any] = {
    "requests_total": 0,
    "requests_by_method": {},
    "requests_by_path": {},
    "errors_total": 0,
}


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Debug mode: %s", settings.debug)
    yield
    logger.info("Shutting down %s", settings.app_name)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Build and return the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered agricultural diagnosis platform providing multimodal "
            "crop disease detection via image, voice, and text analysis."
        ),
        lifespan=lifespan,
    )

    # -- CORS ---------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Metrics middleware ---------------------------------------------------
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        """Increment simple request counters for every HTTP request."""
        _metrics["requests_total"] += 1
        method = request.method
        _metrics["requests_by_method"][method] = _metrics["requests_by_method"].get(method, 0) + 1
        path = request.url.path
        _metrics["requests_by_path"][path] = _metrics["requests_by_path"].get(path, 0) + 1

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        response.headers["X-Process-Time"] = f"{duration:.4f}"
        if response.status_code >= 500:
            _metrics["errors_total"] += 1
        return response

    # -- Routers ------------------------------------------------------------
    app.include_router(health.router)
    app.include_router(routes.router)
    app.include_router(websocket.router)

    # -- Root endpoint ------------------------------------------------------
    @app.get("/", tags=["root"])
    async def root() -> Dict[str, str]:
        """Welcome message for the API root."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
        }

    # -- Metrics endpoint ---------------------------------------------------
    @app.get("/metrics", tags=["monitoring"])
    async def metrics() -> Dict[str, Any]:
        """Return simple in-memory request metrics."""
        return _metrics

    # -- Exception handlers -------------------------------------------------
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("ValueError: %s", exc)
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )

    return app


app = create_app()
