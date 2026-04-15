"""Neo4j graph database loader for agricultural knowledge graphs."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Neo4jLoader:
    """Loads entities and relationships into Neo4j."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
    ) -> None:
        """Initialize the Neo4j loader.

        Args:
            uri: Neo4j connection URI.
            user: Database username.
            password: Database password.
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: Optional[object] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
            logger.info("Connected to Neo4j at %s", self._uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j at %s: %s", self._uri, e)
            self._driver = None

    def load_entities(self, entities: list[dict]) -> int:
        """Load entities into Neo4j using MERGE for idempotency.

        Args:
            entities: List of entity dicts with keys: id, name, type, confidence.

        Returns:
            Number of entities loaded.
        """
        if self._driver is None:
            logger.error("Neo4j driver not connected")
            return 0

        count = 0
        batch_size = 100

        try:
            with self._driver.session() as session:  # type: ignore[union-attr]
                for i in range(0, len(entities), batch_size):
                    batch = entities[i: i + batch_size]
                    result = session.execute_write(self._create_entities_tx, batch)
                    count += result
            logger.info("Loaded %d entities into Neo4j", count)
        except Exception as e:
            logger.error("Failed to load entities: %s", e)

        return count

    def load_relationships(self, relationships: list[dict]) -> int:
        """Load relationships into Neo4j using MERGE for idempotency.

        Args:
            relationships: List of relationship dicts with keys:
                source, target, type, confidence.

        Returns:
            Number of relationships loaded.
        """
        if self._driver is None:
            logger.error("Neo4j driver not connected")
            return 0

        count = 0
        batch_size = 100

        try:
            with self._driver.session() as session:  # type: ignore[union-attr]
                for i in range(0, len(relationships), batch_size):
                    batch = relationships[i: i + batch_size]
                    result = session.execute_write(self._create_relationships_tx, batch)
                    count += result
            logger.info("Loaded %d relationships into Neo4j", count)
        except Exception as e:
            logger.error("Failed to load relationships: %s", e)

        return count

    def batch_load(self, data: dict) -> dict:
        """Load both entities and relationships in batch.

        Args:
            data: Dict with 'entities' and 'relationships' keys.

        Returns:
            Dict with counts: {'entities': int, 'relationships': int}.
        """
        entities = data.get("entities", [])
        relationships = data.get("relationships", [])

        entity_count = self.load_entities(entities)
        rel_count = self.load_relationships(relationships)

        return {"entities": entity_count, "relationships": rel_count}

    @staticmethod
    def _create_entities_tx(tx: object, entities: list[dict]) -> int:
        """Transaction function to create entities.

        Args:
            tx: Neo4j transaction.
            entities: Batch of entities to create.

        Returns:
            Number of entities created.
        """
        count = 0
        for entity in entities:
            query = (
                f"MERGE (e:{entity['type']} {{entity_id: $id}}) "
                "SET e.name = $name, e.confidence = $confidence"
            )
            tx.run(  # type: ignore[union-attr]
                query,
                id=entity["id"],
                name=entity["name"],
                confidence=entity.get("confidence", 0.0),
            )
            count += 1
        return count

    @staticmethod
    def _create_relationships_tx(tx: object, relationships: list[dict]) -> int:
        """Transaction function to create relationships.

        Args:
            tx: Neo4j transaction.
            relationships: Batch of relationships to create.

        Returns:
            Number of relationships created.
        """
        count = 0
        for rel in relationships:
            query = (
                "MATCH (a {entity_id: $source}) "
                "MATCH (b {entity_id: $target}) "
                f"MERGE (a)-[r:{rel['type'].upper()} {{confidence: $confidence}}]->(b)"
            )
            tx.run(  # type: ignore[union-attr]
                query,
                source=rel["source"],
                target=rel["target"],
                confidence=rel.get("confidence", 0.0),
            )
            count += 1
        return count

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()  # type: ignore[union-attr]
            logger.info("Neo4j connection closed")
