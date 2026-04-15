"""Redis-backed caching service with JSON helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import redis.asyncio as aioredis  # type: ignore[import-untyped]

    REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    REDIS_AVAILABLE = False
    logger.warning(
        "redis[async] package not installed – CacheService will be unavailable"
    )


class CacheService:
    """Async Redis cache with transparent JSON serialisation."""

    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        self.redis_url = redis_url
        self.client: Optional[object] = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open an async Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available – cannot connect")
            return

        try:
            self.client = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
            )
            # Verify connectivity
            await self.client.ping()  # type: ignore[union-attr]
            logger.info("Connected to Redis at %s", self.redis_url)
        except ConnectionError:
            logger.error(
                "Could not connect to Redis at %s", self.redis_url
            )
            self.client = None
        except Exception:
            logger.error(
                "Unexpected error connecting to Redis", exc_info=True
            )
            self.client = None

    async def disconnect(self) -> None:
        """Gracefully close the Redis connection."""
        if self.client is not None:
            try:
                await self.client.close()  # type: ignore[union-attr]
                logger.info("Disconnected from Redis")
            except Exception:
                logger.error("Error closing Redis connection", exc_info=True)
            finally:
                self.client = None

    # ------------------------------------------------------------------
    # Primitive operations
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Optional[str]:
        """Retrieve a cached value by *key*."""
        if self.client is None:
            return None
        try:
            value: Optional[str] = await self.client.get(key)  # type: ignore[union-attr]
            return value
        except Exception:
            logger.error("Cache GET failed for key '%s'", key, exc_info=True)
            return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        """Store *value* under *key* with a time-to-live in seconds."""
        if self.client is None:
            return
        try:
            await self.client.set(key, value, ex=ttl)  # type: ignore[union-attr]
        except Exception:
            logger.error("Cache SET failed for key '%s'", key, exc_info=True)

    async def delete(self, key: str) -> None:
        """Remove *key* from the cache."""
        if self.client is None:
            return
        try:
            await self.client.delete(key)  # type: ignore[union-attr]
        except Exception:
            logger.error(
                "Cache DELETE failed for key '%s'", key, exc_info=True
            )

    # ------------------------------------------------------------------
    # JSON helpers
    # ------------------------------------------------------------------

    async def get_json(self, key: str) -> Optional[dict]:
        """Retrieve and deserialise a JSON value."""
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.error(
                "Failed to decode JSON for cache key '%s'", key, exc_info=True
            )
            return None

    async def set_json(self, key: str, value: dict, ttl: int = 3600) -> None:
        """Serialise *value* as JSON and cache it."""
        try:
            raw = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            logger.error(
                "Failed to encode value as JSON for key '%s'",
                key,
                exc_info=True,
            )
            return
        await self.set(key, raw, ttl=ttl)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def generate_cache_key(prefix: str, **kwargs: object) -> str:
        """Build a deterministic cache key from *prefix* and keyword args.

        Keyword arguments are sorted by name, serialised to JSON, then
        SHA-256-hashed to produce a fixed-length suffix.
        """
        sorted_params = json.dumps(kwargs, sort_keys=True, default=str)
        digest = hashlib.sha256(sorted_params.encode()).hexdigest()
        return f"{prefix}:{digest}"

    @property
    def is_connected(self) -> bool:
        """Return ``True`` when a Redis client is available."""
        return self.client is not None
