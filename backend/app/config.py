"""Configuration management for the Agricultural AI Platform.

Uses pydantic-settings to load configuration from environment variables
with sensible defaults for local development.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    app_name: str = "Agricultural AI Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # --- JWT ---
    jwt_secret_key: str = "CHANGE-ME-in-production-use-a-real-secret"  # noqa: S105 — override via JWT_SECRET_KEY env var
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_ttl: int = 3600

    # --- Neo4j ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # --- Qdrant ---
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "agricultural_embeddings"

    # --- EdgeQuake ---
    edgequake_host: str = "localhost"
    edgequake_port: int = 9090

    # --- Vision ---
    vision_model_name: str = "efficientnet_b0"
    vision_confidence_threshold: float = 0.7

    # --- Voice ---
    whisper_model: str = "base"
    voice_language: str = "ar"

    # --- CORS ---
    cors_allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # --- Rate Limiting ---
    requests_per_minute: int = 60

    # --- Logging ---
    log_level: str = "INFO"

    model_config = {"env_prefix": "", "case_sensitive": False}


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
