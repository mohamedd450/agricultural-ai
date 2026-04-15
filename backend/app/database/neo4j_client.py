"""Neo4j async client for the agricultural knowledge graph."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.database.queries import (
    FIND_DISEASE_BY_SYMPTOMS,
    FIND_RELATED_CONDITIONS,
    GET_TREATMENT_FOR_DISEASE,
    GET_DISEASE_GRAPH,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Neo4j driver is optional at import time so the app can still start
# when the database is unavailable.
try:
    from neo4j import AsyncGraphDatabase  # type: ignore[import-untyped]

    _NEO4J_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NEO4J_AVAILABLE = False
    logger.info("neo4j driver not installed – Neo4jClient will operate in stub mode")


class Neo4jClient:
    """Async wrapper around the Neo4j Python driver.

    Usage::

        client = Neo4jClient()
        await client.connect()
        try:
            rows = await client.run_query("MATCH (n) RETURN n LIMIT 5")
        finally:
            await client.close()
    """

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        settings = get_settings()
        self._uri = uri or settings.neo4j_uri
        self._user = user or settings.neo4j_user
        self._password = password or settings.neo4j_password
        self._driver: Any | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the connection pool to Neo4j."""
        if not _NEO4J_AVAILABLE:
            logger.warning("Neo4j driver unavailable – skipping connect")
            return

        try:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", self._uri)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to connect to Neo4j: %s", exc)
            self._driver = None

    async def close(self) -> None:
        """Close the driver and release all pooled connections."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    # ------------------------------------------------------------------
    # Core query execution
    # ------------------------------------------------------------------

    async def run_query(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return all result records as dicts.

        Returns an empty list when the driver is not connected.
        """
        if self._driver is None:
            logger.warning("Neo4j driver not connected – returning empty result")
            return []

        try:
            async with self._driver.session() as session:
                result = await session.run(cypher, parameters=params or {})
                records = await result.data()
                return records  # type: ignore[return-value]
        except Exception as exc:  # noqa: BLE001
            logger.error("Neo4j query failed: %s – %s", cypher[:80], exc)
            return []

    # ------------------------------------------------------------------
    # Domain helpers
    # ------------------------------------------------------------------

    async def get_disease_info(self, disease_name: str) -> dict[str, Any]:
        """Fetch details for a single disease node by name."""
        rows = await self.run_query(
            "MATCH (d:Disease {name: $name}) RETURN d AS disease",
            {"name": disease_name},
        )
        return rows[0] if rows else {}

    async def get_treatment(self, disease_name: str) -> list[dict[str, Any]]:
        """Return treatment options for *disease_name*."""
        return await self.run_query(
            GET_TREATMENT_FOR_DISEASE,
            {"disease_name": disease_name},
        )

    async def get_related_symptoms(self, symptom: str) -> list[dict[str, Any]]:
        """Retrieve diseases and conditions related to *symptom*."""
        return await self.run_query(
            FIND_DISEASE_BY_SYMPTOMS,
            {"symptoms": [symptom], "limit": 10},
        )

    async def find_path(
        self,
        start_node: str,
        end_node: str,
        max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        """Find shortest paths between two named nodes."""
        cypher = (
            "MATCH path = shortestPath("
            "  (a {name: $start})-[*1..$depth]-(b {name: $end})"
            ") "
            "RETURN [n IN nodes(path) | n {.*, labels: labels(n)}] AS nodes, "
            "       [r IN relationships(path) | {type: type(r), "
            "            start: startNode(r).name, end: endNode(r).name}] AS rels, "
            "       length(path) AS hops"
        )
        return await self.run_query(
            cypher,
            {"start": start_node, "end": end_node, "depth": max_depth},
        )
