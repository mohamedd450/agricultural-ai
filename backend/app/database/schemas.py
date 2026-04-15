"""Neo4j schema definitions – constraints, indexes, and label/relationship constants.

These constants are consumed by migration scripts and the :class:`Neo4jClient`
to ensure the graph database schema is consistent and performant.
"""

from __future__ import annotations

# ── Node labels ──────────────────────────────────────────────────────────────

NODE_LABELS: list[str] = [
    "Disease",
    "Symptom",
    "Crop",
    "Fertilizer",
    "WeatherCondition",
    "Treatment",
]

# ── Relationship types ───────────────────────────────────────────────────────

RELATIONSHIP_TYPES: list[str] = [
    "CAUSES",
    "TREATED_BY",
    "WORSENED_BY",
    "TRIGGERED_BY",
    "REQUIRES",
    "IMPROVES_WITH",
]

# ── Uniqueness constraints ───────────────────────────────────────────────────

CREATE_CONSTRAINTS: list[str] = [
    "CREATE CONSTRAINT disease_name_unique IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT symptom_name_unique IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT crop_name_unique IF NOT EXISTS FOR (c:Crop) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT fertilizer_name_unique IF NOT EXISTS FOR (f:Fertilizer) REQUIRE f.name IS UNIQUE",
    "CREATE CONSTRAINT weather_name_unique IF NOT EXISTS FOR (w:WeatherCondition) REQUIRE w.name IS UNIQUE",
    "CREATE CONSTRAINT treatment_name_unique IF NOT EXISTS FOR (t:Treatment) REQUIRE t.name IS UNIQUE",
]

# ── Search indexes ───────────────────────────────────────────────────────────

CREATE_INDEXES: list[str] = [
    "CREATE INDEX disease_arabic_idx IF NOT EXISTS FOR (d:Disease) ON (d.arabic_name)",
    "CREATE INDEX symptom_arabic_idx IF NOT EXISTS FOR (s:Symptom) ON (s.arabic_name)",
    "CREATE INDEX crop_arabic_idx IF NOT EXISTS FOR (c:Crop) ON (c.arabic_name)",
    "CREATE INDEX crop_category_idx IF NOT EXISTS FOR (c:Crop) ON (c.category)",
    "CREATE INDEX fertilizer_type_idx IF NOT EXISTS FOR (f:Fertilizer) ON (f.type)",
    "CREATE INDEX disease_severity_idx IF NOT EXISTS FOR (d:Disease) ON (d.severity)",
    "CREATE INDEX treatment_arabic_idx IF NOT EXISTS FOR (t:Treatment) ON (t.arabic_name)",
    "CREATE INDEX weather_arabic_idx IF NOT EXISTS FOR (w:WeatherCondition) ON (w.arabic_name)",
]
