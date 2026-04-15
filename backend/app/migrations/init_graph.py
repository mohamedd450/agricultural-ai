"""Initialise the Neo4j graph schema – constraints and indexes.

Run this script directly to bootstrap a fresh Neo4j instance::

    python -m app.migrations.init_graph
"""

from __future__ import annotations

import asyncio
import logging

from app.database.neo4j_client import Neo4jClient
from app.database.schemas import CREATE_CONSTRAINTS, CREATE_INDEXES, NODE_LABELS
from app.utils.logger import get_logger, setup_logging

logger: logging.Logger = get_logger(__name__)


async def init_graph_schema(neo4j_client: Neo4jClient) -> None:
    """Create all uniqueness constraints and search indexes.

    Parameters
    ----------
    neo4j_client:
        A connected :class:`Neo4jClient` instance.

    Raises
    ------
    RuntimeError
        If the client is not connected.
    """
    if not neo4j_client.is_connected:
        raise RuntimeError("Neo4j client is not connected. Call connect() first.")

    logger.info("Creating %d constraints …", len(CREATE_CONSTRAINTS))
    for stmt in CREATE_CONSTRAINTS:
        try:
            await neo4j_client.execute_query(stmt)
            logger.debug("OK: %s", stmt[:80])
        except Exception:
            logger.error("Failed to create constraint: %s", stmt[:80], exc_info=True)

    logger.info("Creating %d indexes …", len(CREATE_INDEXES))
    for stmt in CREATE_INDEXES:
        try:
            await neo4j_client.execute_query(stmt)
            logger.debug("OK: %s", stmt[:80])
        except Exception:
            logger.error("Failed to create index: %s", stmt[:80], exc_info=True)

    logger.info("Graph schema initialisation complete")


async def verify_schema(neo4j_client: Neo4jClient) -> bool:
    """Check that all expected constraints exist.

    Parameters
    ----------
    neo4j_client:
        A connected :class:`Neo4jClient` instance.

    Returns
    -------
    bool
        ``True`` when every expected constraint is present.
    """
    if not neo4j_client.is_connected:
        logger.error("Cannot verify schema – Neo4j client is not connected")
        return False

    try:
        records = await neo4j_client.execute_query("SHOW CONSTRAINTS")
        existing_names = {r.get("name", "") for r in records}

        expected_suffixes = [label.lower() + "_name_unique" for label in NODE_LABELS]
        missing = [
            name
            for name in expected_suffixes
            if not any(name in existing for existing in existing_names)
        ]

        if missing:
            logger.warning("Missing constraints: %s", missing)
            return False

        logger.info("Schema verification passed – all constraints present")
        return True
    except Exception:
        logger.error("Schema verification failed", exc_info=True)
        return False


async def _main() -> None:
    """Bootstrap the graph schema from the command line."""
    setup_logging(level="INFO")
    logger.info("Neo4j schema initialisation starting")

    client = Neo4jClient()
    try:
        await client.connect()
        if not client.is_connected:
            logger.error("Could not connect to Neo4j – aborting")
            return

        await init_graph_schema(client)

        ok = await verify_schema(client)
        if ok:
            logger.info("Schema verification: PASSED")
        else:
            logger.warning("Schema verification: FAILED – some items may be missing")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(_main())
