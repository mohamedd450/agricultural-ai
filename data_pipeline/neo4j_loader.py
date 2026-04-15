from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from neo4j import AsyncGraphDatabase
except ImportError:
    AsyncGraphDatabase = None  # type: ignore[assignment, misc]


class Neo4jLoader:
    """Load agricultural knowledge-graph data into Neo4j."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None

    async def connect(self) -> None:
        """Establish a connection to the Neo4j database."""
        if AsyncGraphDatabase is None:
            raise RuntimeError(
                "neo4j driver is not installed. Run: pip install neo4j"
            )

        self._driver = AsyncGraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )
        logger.info("Connected to Neo4j at %s", self.uri)

    async def load_entities(self, entities: list[dict]) -> int:
        """Create nodes for each entity.

        Each entity dict must contain ``name`` and ``type`` keys.
        Returns the number of nodes created.
        """
        if self._driver is None:
            raise RuntimeError("Not connected. Call connect() first.")

        count = 0
        async with self._driver.session() as session:
            for entity in entities:
                try:
                    await session.run(
                        "MERGE (e:Entity {name: $name}) "
                        "SET e.type = $type, e.context = $context",
                        name=entity.get("name", ""),
                        type=entity.get("type", "unknown"),
                        context=entity.get("context", ""),
                    )
                    count += 1
                except Exception:
                    logger.exception(
                        "Failed to create node for entity: %s",
                        entity.get("name"),
                    )

        logger.info("Created %d entity nodes in Neo4j", count)
        return count

    async def load_relationships(self, relationships: list[dict]) -> int:
        """Create edges between entity nodes.

        Each relationship dict must contain ``source``, ``target``,
        ``relationship``, and ``confidence`` keys.
        Returns the number of relationships created.
        """
        if self._driver is None:
            raise RuntimeError("Not connected. Call connect() first.")

        count = 0
        async with self._driver.session() as session:
            for rel in relationships:
                try:
                    await session.run(
                        "MATCH (a:Entity {name: $source}) "
                        "MATCH (b:Entity {name: $target}) "
                        "MERGE (a)-[r:RELATED_TO {type: $rel_type}]->(b) "
                        "SET r.confidence = $confidence",
                        source=rel.get("source", ""),
                        target=rel.get("target", ""),
                        rel_type=rel.get("relationship", ""),
                        confidence=rel.get("confidence", 0.0),
                    )
                    count += 1
                except Exception:
                    logger.exception(
                        "Failed to create relationship: %s -> %s",
                        rel.get("source"),
                        rel.get("target"),
                    )

        logger.info("Created %d relationships in Neo4j", count)
        return count

    async def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed.")
