"""Parameterised Cypher query templates for the agricultural knowledge graph.

All queries use Neo4j parameter syntax (``$param``) to prevent injection and
enable query-plan caching on the server side.
"""

from __future__ import annotations

# ── Disease lookups ──────────────────────────────────────────────────────────

FIND_DISEASE_BY_NAME: str = """
MATCH (d:Disease)
WHERE d.name = $name OR d.arabic_name = $name
RETURN d {.*} AS disease
LIMIT 1
"""

FIND_DISEASE_BY_SYMPTOM: str = """
MATCH (s:Symptom)-[:CAUSES]->(d:Disease)
WHERE s.name = $symptom OR s.arabic_name = $symptom
RETURN d {.*} AS disease, s {.*} AS symptom
"""

FIND_TREATMENTS_FOR_DISEASE: str = """
MATCH (d:Disease)-[:TREATED_BY]->(t:Treatment)
WHERE d.name = $disease_name OR d.arabic_name = $disease_name
RETURN t {.*} AS treatment
"""

# ── Crop lookups ─────────────────────────────────────────────────────────────

FIND_CROP_DISEASES: str = """
MATCH (c:Crop)<-[:TRIGGERED_BY]-(d:Disease)
WHERE c.name = $crop_name OR c.arabic_name = $crop_name
RETURN d {.*} AS disease, c {.*} AS crop
"""

# ── Graph traversal ──────────────────────────────────────────────────────────

GET_GRAPH_PATHS: str = """
MATCH path = (start)-[*1..$depth]-(end)
WHERE start.name = $name OR start.arabic_name = $name
RETURN [node IN nodes(path) | node {.*}] AS nodes,
       [rel IN relationships(path) | type(rel)] AS relationships
LIMIT $limit
"""

GET_NODE_NEIGHBORHOOD: str = """
MATCH (center)-[r]-(neighbor)
WHERE center.name = $node_name OR center.arabic_name = $node_name
WITH center, r, neighbor
LIMIT 50
RETURN collect(DISTINCT center {.*, _labels: labels(center)}) AS center_nodes,
       collect(DISTINCT {
           source: center.name,
           target: neighbor.name,
           relationship: type(r)
       }) AS edges,
       collect(DISTINCT neighbor {.*, _labels: labels(neighbor)}) AS neighbor_nodes
"""

# ── Write operations ─────────────────────────────────────────────────────────

CREATE_DISEASE: str = """
MERGE (d:Disease {name: $name})
ON CREATE SET d.arabic_name = $arabic_name,
              d.description = $description,
              d.severity = $severity,
              d.created_at = datetime()
ON MATCH SET  d.arabic_name = $arabic_name,
              d.description = $description,
              d.severity = $severity,
              d.updated_at = datetime()
RETURN d {.*} AS disease
"""

CREATE_SYMPTOM: str = """
MERGE (s:Symptom {name: $name})
ON CREATE SET s.arabic_name = $arabic_name,
              s.visual_description = $visual_description,
              s.created_at = datetime()
ON MATCH SET  s.arabic_name = $arabic_name,
              s.visual_description = $visual_description,
              s.updated_at = datetime()
RETURN s {.*} AS symptom
"""

CREATE_RELATIONSHIP: str = """
MATCH (source {name: $source_name})
MATCH (target {name: $target_name})
CALL apoc.merge.relationship(source, $relationship_type, {}, {confidence: $confidence, created_at: datetime()}, target)
YIELD rel
RETURN type(rel) AS relationship, source.name AS source, target.name AS target
"""
