"""Neo4j graph database initialisation.

Creates constraints, indexes, and node types for the agricultural
knowledge graph.  All operations use ``MERGE`` so the script is safe
to run multiple times (idempotent).
"""

import logging

logger = logging.getLogger(__name__)

# Constraints and indexes to create on first run
_CONSTRAINTS = [
    ("disease_name", "Disease", "name"),
    ("symptom_name", "Symptom", "name"),
    ("crop_name", "Crop", "name"),
    ("fertilizer_name", "Fertilizer", "name"),
    ("weather_name", "Weather", "name"),
    ("region_name", "Region", "name"),
]

_INDEXES = [
    ("idx_disease_severity", "Disease", "severity"),
    ("idx_crop_season", "Crop", "season"),
    ("idx_region_climate", "Region", "climate"),
]

# Seed nodes to ensure the core label types exist in the graph
_SEED_NODES: list[tuple[str, dict]] = [
    ("Disease", {"name": "Unknown Disease", "severity": "unknown"}),
    ("Symptom", {"name": "Unknown Symptom"}),
    ("Crop", {"name": "Unknown Crop"}),
    ("Fertilizer", {"name": "Unknown Fertilizer"}),
    ("Weather", {"name": "Unknown Weather"}),
    ("Region", {"name": "Unknown Region"}),
]

# Sample relationships between seed nodes
_SEED_RELATIONSHIPS = [
    ("Disease", "Unknown Disease", "AFFECTS", "Crop", "Unknown Crop"),
    ("Weather", "Unknown Weather", "TRIGGERS", "Disease", "Unknown Disease"),
    ("Fertilizer", "Unknown Fertilizer", "TREATS", "Disease", "Unknown Disease"),
    ("Disease", "Unknown Disease", "SHOWS", "Symptom", "Unknown Symptom"),
]


async def init_graph(neo4j_driver) -> None:
    """Initialise the Neo4j agricultural knowledge graph.

    Creates uniqueness constraints, performance indexes, seed node
    types, and sample relationships.  Every statement uses ``MERGE``
    so this function is safe to call repeatedly.

    Args:
        neo4j_driver: An open ``neo4j.AsyncDriver`` instance.
    """
    logger.info("Starting graph initialisation")

    async with neo4j_driver.session() as session:
        # -- Constraints ------------------------------------------------
        for constraint_name, label, prop in _CONSTRAINTS:
            cypher = (
                f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            try:
                await session.run(cypher)
                logger.info("Constraint OK: %s on %s.%s", constraint_name, label, prop)
            except Exception:
                logger.warning(
                    "Constraint %s may already exist – skipping", constraint_name
                )

        # -- Indexes ----------------------------------------------------
        for index_name, label, prop in _INDEXES:
            cypher = (
                f"CREATE INDEX {index_name} IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.{prop})"
            )
            try:
                await session.run(cypher)
                logger.info("Index OK: %s on %s.%s", index_name, label, prop)
            except Exception:
                logger.warning("Index %s may already exist – skipping", index_name)

        # -- Seed nodes -------------------------------------------------
        for label, props in _SEED_NODES:
            props_str = ", ".join(f"{k}: ${k}" for k in props)
            cypher = f"MERGE (n:{label} {{{props_str}}})"
            await session.run(cypher, props)
            logger.info("Seed node MERGE: (:%s {name: %s})", label, props["name"])

        # -- Sample relationships ----------------------------------------
        for src_label, src_name, rel, tgt_label, tgt_name in _SEED_RELATIONSHIPS:
            cypher = (
                f"MATCH (a:{src_label} {{name: $src_name}}) "
                f"MATCH (b:{tgt_label} {{name: $tgt_name}}) "
                f"MERGE (a)-[:{rel}]->(b)"
            )
            await session.run(cypher, {"src_name": src_name, "tgt_name": tgt_name})
            logger.info(
                "Relationship MERGE: (:%s %s)-[:%s]->(:%s %s)",
                src_label, src_name, rel, tgt_label, tgt_name,
            )

    logger.info("Graph initialisation complete")
