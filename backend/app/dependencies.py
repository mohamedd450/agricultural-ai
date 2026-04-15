"""Dependency injection helpers for FastAPI route handlers.

Each ``get_*`` function returns a cached singleton of the corresponding
service, suitable for use with :func:`fastapi.Depends`.
"""

from __future__ import annotations

from functools import lru_cache

from app.services.vision_service import VisionService
from app.services.voice_service import VoiceService
from app.services.graph_rag_service import GraphRAGService
from app.services.vector_db_service import VectorDBService
from app.services.decision_router import DecisionRouter
from app.services.fusion_service import FusionService
from app.services.cache_service import CacheService
from app.database.neo4j_client import Neo4jClient


@lru_cache()
def get_vision_service() -> VisionService:
    """Return a cached :class:`VisionService` instance."""
    return VisionService()


@lru_cache()
def get_voice_service() -> VoiceService:
    """Return a cached :class:`VoiceService` instance."""
    return VoiceService()


@lru_cache()
def get_graph_rag_service() -> GraphRAGService:
    """Return a cached :class:`GraphRAGService` instance."""
    return GraphRAGService()


@lru_cache()
def get_vector_db_service() -> VectorDBService:
    """Return a cached :class:`VectorDBService` instance."""
    return VectorDBService()


@lru_cache()
def get_decision_router() -> DecisionRouter:
    """Return a cached :class:`DecisionRouter` instance."""
    return DecisionRouter()


@lru_cache()
def get_fusion_service() -> FusionService:
    """Return a cached :class:`FusionService` instance."""
    return FusionService()


@lru_cache()
def get_cache_service() -> CacheService:
    """Return a cached :class:`CacheService` instance."""
    return CacheService()


@lru_cache()
def get_neo4j_client() -> Neo4jClient:
    """Return a cached :class:`Neo4jClient` instance."""
    return Neo4jClient()
