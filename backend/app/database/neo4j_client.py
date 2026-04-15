"""Async Neo4j client for the agricultural knowledge graph.

Wraps the official ``neo4j`` async driver, providing typed helpers for
common graph queries used throughout the platform.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.config import get_settings
from app.utils.logger import get_logger

logger: logging.Logger = get_logger(__name__)

try:
    from neo4j import AsyncGraphDatabase
except ImportError:  # pragma: no cover
    AsyncGraphDatabase = None  # type: ignore[assignment,misc]
    logger.warning("neo4j driver not installed – Neo4jClient will be non-functional")


class Neo4jClient:
    """Async wrapper around the Neo4j Python driver.

    Parameters
    ----------
    uri:
        Bolt URI for the Neo4j instance.  Falls back to settings when *None*.
    user:
        Database user.  Falls back to settings when *None*.
    password:
        Database password.  Falls back to settings when *None*.
    """

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        settings = get_settings()
        self._uri: str = uri or settings.neo4j_uri
        self._user: str = user or settings.neo4j_user
        self._password: str = password or settings.neo4j_password
        self._driver: Any = None

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Open a connection pool to Neo4j."""
        if AsyncGraphDatabase is None:
            logger.error("Cannot connect: neo4j driver is not installed")
            return
        try:
            self._driver = AsyncGraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
            await self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", self._uri)
        except Exception:
            logger.exception("Failed to connect to Neo4j at %s", self._uri)
            self._driver = None

    async def close(self) -> None:
        """Gracefully close the Neo4j driver."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @property
    def is_connected(self) -> bool:
        """Return ``True`` when the driver has been initialised."""
        return self._driver is not None

    # ── Generic query execution ──────────────────────────────────────────

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return the result records as dicts.

        Parameters
        ----------
        query:
            Parameterised Cypher query string.
        parameters:
            Mapping of parameter names to values.

        Returns
        -------
        list[dict[str, Any]]
            Each record converted to a plain dictionary.

        Raises
        ------
        RuntimeError
            If the driver is not connected.
        """
        if not self.is_connected:
            raise RuntimeError("Neo4j driver is not connected. Call connect() first.")

        try:
            async with self._driver.session() as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                logger.debug(
                    "Executed query (%d results): %s",
                    len(records),
                    query[:120],
                )
                return records
        except Exception:
            logger.exception("Neo4j query failed: %s", query[:120])
            raise

    # ── Domain helpers ───────────────────────────────────────────────────

    async def find_disease(self, name: str) -> Optional[dict[str, Any]]:
        """Look up a disease by name (English or Arabic).

        Returns
        -------
        dict or None
            Disease properties, or *None* when not found.
        """
        from app.database.queries import FIND_DISEASE_BY_NAME

        records = await self.execute_query(FIND_DISEASE_BY_NAME, {"name": name})
        if records:
            return records[0].get("disease")
        return None

    async def find_treatments(self, disease_name: str) -> list[dict[str, Any]]:
        """Return treatments linked to *disease_name*."""
        from app.database.queries import FIND_TREATMENTS_FOR_DISEASE

        records = await self.execute_query(
            FIND_TREATMENTS_FOR_DISEASE,
            {"disease_name": disease_name},
        )
        return [r["treatment"] for r in records if "treatment" in r]

    async def find_symptoms(self, crop_name: str) -> list[dict[str, Any]]:
        """Return diseases (and their triggering symptoms) for *crop_name*.

        Although the relationship ``TRIGGERED_BY`` links crops to diseases,
        this helper bridges the gap so callers can discover symptoms
        associated with a given crop through its diseases.
        """
        from app.database.queries import FIND_CROP_DISEASES

        records = await self.execute_query(
            FIND_CROP_DISEASES,
            {"crop_name": crop_name},
        )
        return [r["disease"] for r in records if "disease" in r]

    async def get_graph_neighborhood(
        self,
        node_name: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        """Return the local neighbourhood of a node for visualisation.

        Parameters
        ----------
        node_name:
            ``name`` property of the centre node.
        depth:
            Maximum traversal depth (default 2).

        Returns
        -------
        dict
            ``{"nodes": [...], "edges": [...]}`` suitable for frontend
            graph rendering.
        """
        from app.database.queries import GET_NODE_NEIGHBORHOOD

        records = await self.execute_query(
            GET_NODE_NEIGHBORHOOD,
            {"node_name": node_name},
        )

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for record in records:
            for node in record.get("center_nodes", []):
                name = node.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    nodes.append(node)

            for node in record.get("neighbor_nodes", []):
                name = node.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    nodes.append(node)

            edges.extend(record.get("edges", []))

        return {"nodes": nodes, "edges": edges}
