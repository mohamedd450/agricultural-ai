"""Parameterised Cypher queries for the agricultural knowledge graph."""

from typing import Final

# ---------------------------------------------------------------------------
# Disease / Symptom queries
# ---------------------------------------------------------------------------

FIND_DISEASE_BY_SYMPTOMS: Final[str] = """
MATCH (s:Symptom)-[:causes]->(d:Disease)
WHERE s.name IN $symptoms
WITH d, count(s) AS matched
ORDER BY matched DESC
LIMIT $limit
RETURN d {.*, matched: matched} AS disease
"""

GET_TREATMENT_FOR_DISEASE: Final[str] = """
MATCH (d:Disease {name: $disease_name})-[:treated_by]->(t)
RETURN t {.*, relationship: 'treated_by'} AS treatment
ORDER BY t.priority ASC
"""

GET_CROP_DISEASES: Final[str] = """
MATCH (c:Crop {name: $crop_name})<-[:affects]-(d:Disease)
RETURN d {.*, crop: c.name} AS disease
ORDER BY d.severity DESC
"""

FIND_RELATED_CONDITIONS: Final[str] = """
MATCH (d:Disease {name: $disease_name})-[r]-(related)
WHERE type(r) IN ['worsened_by', 'triggered_by', 'causes']
RETURN related {.*, relationship: type(r), direction: CASE
    WHEN startNode(r) = d THEN 'outgoing'
    ELSE 'incoming'
END} AS condition
"""

# ---------------------------------------------------------------------------
# Multi-hop / graph traversal
# ---------------------------------------------------------------------------

GET_DISEASE_GRAPH: Final[str] = """
MATCH path = (start {name: $entity_name})-[*1..$max_depth]-(end)
WHERE any(label IN labels(start) WHERE label IN
      ['Disease', 'Symptom', 'Crop', 'Fertilizer', 'Weather'])
WITH path, length(path) AS hops
ORDER BY hops ASC
LIMIT $limit
RETURN [node IN nodes(path) | node {.*, labels: labels(node)}] AS nodes,
       [rel IN relationships(path) | {type: type(rel),
            start: startNode(rel).name,
            end: endNode(rel).name}] AS relationships,
       hops
"""

# ---------------------------------------------------------------------------
# Fertilizer & recommendations
# ---------------------------------------------------------------------------

GET_FERTILIZER_RECOMMENDATIONS: Final[str] = """
MATCH (c:Crop {name: $crop_name})-[:treated_by]->(f:Fertilizer)
OPTIONAL MATCH (f)-[:worsened_by]->(w:Weather)
RETURN f {.*, crop: c.name,
       weather_warnings: collect(DISTINCT w.name)} AS fertilizer
ORDER BY f.effectiveness DESC
"""

# ---------------------------------------------------------------------------
# Full-text / keyword search
# ---------------------------------------------------------------------------

SEARCH_BY_KEYWORD: Final[str] = """
MATCH (n)
WHERE any(label IN labels(n) WHERE label IN
      ['Disease', 'Symptom', 'Crop', 'Fertilizer', 'Weather'])
  AND (toLower(n.name) CONTAINS toLower($keyword)
       OR toLower(coalesce(n.description, '')) CONTAINS toLower($keyword))
RETURN n {.*, labels: labels(n)} AS result
ORDER BY n.name ASC
LIMIT $limit
"""
