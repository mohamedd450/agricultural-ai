"""Redis caching service with graceful degradation.

Provides get / set / delete operations backed by Redis.  When Redis is
unavailable every operation silently returns a safe default so that the
rest of the application can continue without interruption.
"""

import hashlib
import json
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-backed cache with JSON serialisation.

    All public methods handle connection failures gracefully – a
    missing or crashed Redis instance will never raise an exception
    to the caller.

    Args:
        redis_client: Optional async Redis client (for testing or
            dependency injection).  When *None* the service operates
            in "no-op" mode and every read returns ``None``.
    """

    def __init__(self, redis_client: Any = None) -> None:
        self._settings = get_settings()
        self._redis = redis_client
        self._default_ttl: int = self._settings.redis_ttl

        logger.info(
            "CacheService initialised (connected=%s, default_ttl=%ds)",
            self._redis is not None,
            self._default_ttl,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get(self, key: str) -> dict | None:
        """Retrieve a cached value.

        Args:
            key: The cache key.

        Returns:
            The deserialised dict, or ``None`` if the key is missing
            or Redis is unavailable.
        """
        if self._redis is None:
            logger.debug("Cache GET skipped – no Redis client")
            return None

        try:
            raw: bytes | None = await self._redis.get(key)
            if raw is None:
                logger.debug("Cache MISS: %s", key)
                return None
            value = json.loads(raw)
            logger.debug("Cache HIT: %s", key)
            return value
        except json.JSONDecodeError:
            logger.warning("Cache GET – invalid JSON for key '%s'", key)
            return None
        except Exception:
            logger.warning("Cache GET failed for key '%s'", key, exc_info=True)
            return None

    async def set(
        self, key: str, value: dict, ttl: int | None = None
    ) -> bool:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: A JSON-serialisable dict.
            ttl: Time-to-live in seconds.  Defaults to the configured
                ``redis_ttl``.

        Returns:
            ``True`` on success, ``False`` otherwise.
        """
        if self._redis is None:
            logger.debug("Cache SET skipped – no Redis client")
            return False

        if ttl is None:
            ttl = self._default_ttl

        try:
            serialised = json.dumps(value, default=str)
            await self._redis.set(key, serialised, ex=ttl)
            logger.debug("Cache SET: %s (ttl=%ds)", key, ttl)
            return True
        except (TypeError, ValueError) as exc:
            logger.warning("Cache SET – serialisation error: %s", exc)
            return False
        except Exception:
            logger.warning("Cache SET failed for key '%s'", key, exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        """Remove a key from the cache.

        Args:
            key: The cache key to delete.

        Returns:
            ``True`` if the key was deleted, ``False`` otherwise.
        """
        if self._redis is None:
            logger.debug("Cache DELETE skipped – no Redis client")
            return False

        try:
            result = await self._redis.delete(key)
            deleted = result > 0
            logger.debug("Cache DELETE: %s (removed=%s)", key, deleted)
            return deleted
        except Exception:
            logger.warning("Cache DELETE failed for key '%s'", key, exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Key generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_cache_key(
        query: str, image_hash: str | None = None
    ) -> str:
        """Derive a deterministic cache key from query text and optional image hash.

        Args:
            query: The query string.
            image_hash: Optional hex digest of the image contents.

        Returns:
            A ``"cache:"``-prefixed SHA-256 key.
        """
        raw = query.strip().lower()
        if image_hash:
            raw = f"{raw}:{image_hash}"
        digest = hashlib.sha256(raw.encode()).hexdigest()
        return f"cache:{digest}"
