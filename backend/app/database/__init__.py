"""Database clients and schema helpers for the Agricultural AI Platform."""

from app.database.neo4j_client import Neo4jClient
from app.database.queries import (
    FIND_DISEASE_BY_SYMPTOMS,
    FIND_RELATED_CONDITIONS,
    GET_CROP_DISEASES,
    GET_DISEASE_GRAPH,
    GET_FERTILIZER_RECOMMENDATIONS,
    GET_TREATMENT_FOR_DISEASE,
    SEARCH_BY_KEYWORD,
)
from app.database.schemas import initialize_schema

__all__ = [
    "FIND_DISEASE_BY_SYMPTOMS",
    "FIND_RELATED_CONDITIONS",
    "GET_CROP_DISEASES",
    "GET_DISEASE_GRAPH",
    "GET_FERTILIZER_RECOMMENDATIONS",
    "GET_TREATMENT_FOR_DISEASE",
    "Neo4jClient",
    "SEARCH_BY_KEYWORD",
    "initialize_schema",
]
