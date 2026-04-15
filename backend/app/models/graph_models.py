"""Pydantic models for knowledge-graph data structures."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GraphNode(BaseModel):
    """A single node in the agricultural knowledge graph."""

    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Human-readable node label")
    type: Literal["Disease", "Symptom", "Crop", "Fertilizer", "Weather"] = Field(
        ..., description="Node category"
    )
    properties: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Arbitrary key-value properties"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Optional confidence score (0-1)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "disease-001",
                    "label": "Early Blight",
                    "type": "Disease",
                    "properties": {"scientific_name": "Alternaria solani"},
                    "confidence": 0.95,
                }
            ]
        }
    )


class GraphEdge(BaseModel):
    """A directed edge between two knowledge-graph nodes."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: Literal[
        "causes", "treated_by", "worsened_by", "triggered_by", "affects"
    ] = Field(..., description="Edge relationship type")
    weight: float = Field(..., ge=0.0, le=1.0, description="Edge weight / strength (0-1)")
    properties: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Arbitrary key-value properties"
    )

    @field_validator("source", "target")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Node ID must not be empty")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source": "symptom-010",
                    "target": "disease-001",
                    "relationship": "causes",
                    "weight": 0.85,
                    "properties": {"evidence": "field observation"},
                }
            ]
        }
    )


class GraphPath(BaseModel):
    """An ordered path through the knowledge graph."""

    nodes: list[GraphNode] = Field(..., min_length=1, description="Ordered nodes in the path")
    edges: list[GraphEdge] = Field(default_factory=list, description="Edges connecting the nodes")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall path confidence (0-1)")
    description: str = Field(..., description="Human-readable description of this reasoning path")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nodes": [
                        {
                            "id": "symptom-010",
                            "label": "Yellow spots",
                            "type": "Symptom",
                            "properties": {},
                            "confidence": 0.9,
                        },
                        {
                            "id": "disease-001",
                            "label": "Early Blight",
                            "type": "Disease",
                            "properties": {"scientific_name": "Alternaria solani"},
                            "confidence": 0.95,
                        },
                    ],
                    "edges": [
                        {
                            "source": "symptom-010",
                            "target": "disease-001",
                            "relationship": "causes",
                            "weight": 0.85,
                            "properties": {},
                        }
                    ],
                    "confidence": 0.88,
                    "description": "Yellow spots are a key indicator of early blight.",
                }
            ]
        }
    )


class KnowledgeSubgraph(BaseModel):
    """A relevant subgraph extracted from the full knowledge graph."""

    nodes: list[GraphNode] = Field(default_factory=list, description="Nodes in the subgraph")
    edges: list[GraphEdge] = Field(default_factory=list, description="Edges in the subgraph")
    paths: list[GraphPath] = Field(
        default_factory=list, description="Notable reasoning paths within the subgraph"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nodes": [
                        {
                            "id": "crop-001",
                            "label": "Tomato",
                            "type": "Crop",
                            "properties": {},
                            "confidence": None,
                        }
                    ],
                    "edges": [],
                    "paths": [],
                }
            ]
        }
    )


class GraphRAGResponse(BaseModel):
    """Response from the Graph RAG retrieval and generation pipeline."""

    answer: str = Field(..., description="Generated natural-language answer")
    graph_paths: list[str] = Field(
        default_factory=list, description="Human-readable graph path summaries"
    )
    subgraph: Optional[KnowledgeSubgraph] = Field(
        None, description="Relevant knowledge subgraph, if requested"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall answer confidence (0-1)")
    reasoning_steps: list[str] = Field(
        default_factory=list, description="Step-by-step reasoning trace"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": "Early blight in tomatoes is caused by the fungus Alternaria solani.",
                    "graph_paths": [
                        "Tomato -> susceptible_to -> Early Blight",
                        "Early Blight -> caused_by -> Alternaria solani",
                    ],
                    "subgraph": None,
                    "confidence": 0.91,
                    "reasoning_steps": [
                        "Identified crop: Tomato",
                        "Matched symptoms to Early Blight",
                        "Retrieved causal agent from knowledge graph",
                    ],
                }
            ]
        }
    )
