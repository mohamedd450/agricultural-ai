"""Application configuration module.

Centralised settings management using Pydantic BaseSettings.  All values are
loaded from environment variables (or an ``.env`` file) with sensible defaults
suitable for local development.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Root configuration object for the Agricultural AI platform."""

    # ── General ──────────────────────────────────────────────────────────
    app_name: str = Field(default="Agricultural AI Platform")
    debug: bool = Field(default=False)
    api_prefix: str = Field(default="/api/v1")
    log_level: str = Field(default="INFO")

    # ── Authentication / JWT ─────────────────────────────────────────────
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiry_minutes: int = Field(default=30)

    # ── Redis ────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── Neo4j ────────────────────────────────────────────────────────────
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="neo4j")

    # ── Qdrant (vector DB) ───────────────────────────────────────────────
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_collection: str = Field(default="agricultural_embeddings")

    # ── External services ────────────────────────────────────────────────
    edgequake_endpoint: str = Field(default="http://localhost:8081/edgequake")
    whisper_model_size: str = Field(default="base")
    vision_model_name: str = Field(default="efficientnet_b0")

    # ── Rate limiting ────────────────────────────────────────────────────
    rate_limit_per_minute: int = Field(default=100)

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # ── Observability ────────────────────────────────────────────────────
    prometheus_enabled: bool = Field(default=True)

    class Config:  # noqa: D106
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Using :func:`functools.lru_cache` ensures the ``.env`` file is read at
    most once per process lifetime.
    """
    return Settings()
