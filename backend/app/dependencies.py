"""FastAPI dependency injection for external service clients.

Each dependency yields a client instance and gracefully handles connection
failures by logging a warning and yielding *None* so that endpoints can
degrade instead of crashing.
"""

import logging
from typing import AsyncGenerator, Optional

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------
async def get_redis_client(
    settings: Optional[Settings] = None,
) -> AsyncGenerator[Optional[object], None]:
    """Yield an async Redis client, or *None* if Redis is unavailable.

    Usage as a FastAPI dependency::

        @router.get("/example")
        async def example(redis=Depends(get_redis_client)):
            ...
    """
    settings = settings or get_settings()
    client = None
    try:
        import redis.asyncio as aioredis

        client = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )
        # Quick connectivity check
        await client.ping()
        logger.info("Redis connection established (%s:%s)", settings.redis_host, settings.redis_port)
        yield client
    except Exception as exc:
        logger.warning("Redis unavailable – falling back to None: %s", exc)
        yield None
    finally:
        if client is not None:
            await client.aclose()


# ---------------------------------------------------------------------------
# Neo4j
# ---------------------------------------------------------------------------
async def get_neo4j_driver(
    settings: Optional[Settings] = None,
) -> AsyncGenerator[Optional[object], None]:
    """Yield a Neo4j driver, or *None* if Neo4j is unavailable.

    The driver is closed when the request scope ends.
    """
    settings = settings or get_settings()
    driver = None
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        driver.verify_connectivity()
        logger.info("Neo4j connection established (%s)", settings.neo4j_uri)
        yield driver
    except Exception as exc:
        logger.warning("Neo4j unavailable – falling back to None: %s", exc)
        yield None
    finally:
        if driver is not None:
            driver.close()


# ---------------------------------------------------------------------------
# Qdrant
# ---------------------------------------------------------------------------
async def get_qdrant_client(
    settings: Optional[Settings] = None,
) -> AsyncGenerator[Optional[object], None]:
    """Yield a Qdrant client, or *None* if Qdrant is unavailable.

    The client is closed when the request scope ends.
    """
    settings = settings or get_settings()
    client = None
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        # Lightweight health check
        client.get_collections()
        logger.info("Qdrant connection established (%s:%s)", settings.qdrant_host, settings.qdrant_port)
        yield client
    except Exception as exc:
        logger.warning("Qdrant unavailable – falling back to None: %s", exc)
        yield None
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
