"""Neo4j schema definitions – constraints, indexes, and node templates."""

from __future__ import annotations

from typing import Final

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Unique-property constraints
# ---------------------------------------------------------------------------

CONSTRAINT_STATEMENTS: Final[list[str]] = [
    "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT crop_name IF NOT EXISTS FOR (c:Crop) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT fertilizer_name IF NOT EXISTS FOR (f:Fertilizer) REQUIRE f.name IS UNIQUE",
    "CREATE CONSTRAINT weather_name IF NOT EXISTS FOR (w:Weather) REQUIRE w.name IS UNIQUE",
]

# ---------------------------------------------------------------------------
# Indexes for common look-ups
# ---------------------------------------------------------------------------

INDEX_STATEMENTS: Final[list[str]] = [
    "CREATE INDEX disease_severity IF NOT EXISTS FOR (d:Disease) ON (d.severity)",
    "CREATE INDEX symptom_category IF NOT EXISTS FOR (s:Symptom) ON (s.category)",
    "CREATE INDEX crop_type IF NOT EXISTS FOR (c:Crop) ON (c.type)",
    "CREATE INDEX fertilizer_type IF NOT EXISTS FOR (f:Fertilizer) ON (f.type)",
    "CREATE INDEX weather_condition IF NOT EXISTS FOR (w:Weather) ON (w.condition)",
]

# ---------------------------------------------------------------------------
# Node creation templates (parameterised Cypher)
# ---------------------------------------------------------------------------

NODE_TEMPLATES: Final[dict[str, str]] = {
    "Disease": (
        "MERGE (d:Disease {name: $name}) "
        "SET d.description = $description, "
        "    d.severity = $severity, "
        "    d.category = $category, "
        "    d.updated_at = datetime()"
    ),
    "Symptom": (
        "MERGE (s:Symptom {name: $name}) "
        "SET s.description = $description, "
        "    s.category = $category, "
        "    s.updated_at = datetime()"
    ),
    "Crop": (
        "MERGE (c:Crop {name: $name}) "
        "SET c.type = $type, "
        "    c.season = $season, "
        "    c.region = $region, "
        "    c.updated_at = datetime()"
    ),
    "Fertilizer": (
        "MERGE (f:Fertilizer {name: $name}) "
        "SET f.type = $type, "
        "    f.application_method = $application_method, "
        "    f.effectiveness = $effectiveness, "
        "    f.updated_at = datetime()"
    ),
    "Weather": (
        "MERGE (w:Weather {name: $name}) "
        "SET w.condition = $condition, "
        "    w.severity = $severity, "
        "    w.updated_at = datetime()"
    ),
}


# ---------------------------------------------------------------------------
# Schema initialisation helper
# ---------------------------------------------------------------------------

async def initialize_schema(neo4j_client) -> None:
    """Apply all constraints and indexes to the Neo4j database.

    Parameters
    ----------
    neo4j_client:
        An instance of :class:`app.database.neo4j_client.Neo4jClient` (or any
        object exposing an ``async run_query(cypher, params)`` method).
    """
    logger.info("Initialising Neo4j schema (constraints + indexes)…")

    for stmt in CONSTRAINT_STATEMENTS:
        try:
            await neo4j_client.run_query(stmt)
            logger.debug("Applied: %s", stmt[:60])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Constraint may already exist: %s – %s", stmt[:60], exc)

    for stmt in INDEX_STATEMENTS:
        try:
            await neo4j_client.run_query(stmt)
            logger.debug("Applied: %s", stmt[:60])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Index may already exist: %s – %s", stmt[:60], exc)

    logger.info("Neo4j schema initialisation complete.")
