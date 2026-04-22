"""Response models for the Agricultural AI platform API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class DiagnosisResponse(BaseModel):
    """Response containing a crop disease diagnosis and treatment plan."""

    diagnosis: str = Field(..., description="Identified disease or condition.")
    treatment: str = Field(..., description="Recommended treatment or action plan.")
    confidence: float = Field(..., description="Model confidence score (0.0–1.0).")
    graph_paths: list[str] = Field(
        ..., description="Knowledge-graph traversal paths used for the diagnosis."
    )
    explanation: str = Field(
        ..., description="Human-readable explanation of the diagnosis reasoning."
    )
    source: str = Field(
        ..., description="Data source or model that produced the diagnosis."
    )
    language: str = Field(..., description="Language of the response content.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when the diagnosis was generated.",
    )


class VoiceResponse(BaseModel):
    """Response for voice-based interactions."""

    text_response: str = Field(..., description="Textual form of the spoken response.")
    audio_url: Optional[str] = Field(
        default=None, description="URL to the generated audio response file."
    )
    diagnosis: Optional[DiagnosisResponse] = Field(
        default=None, description="Full diagnosis details, if applicable."
    )


class HealthResponse(BaseModel):
    """Health-check response indicating service status."""

    status: str = Field(..., description="Overall system health status.")
    services: dict[str, str] = Field(
        ..., description="Per-service health statuses."
    )
    timestamp: datetime = Field(
        ..., description="UTC timestamp of the health check."
    )


class TokenResponse(BaseModel):
    """OAuth2-compatible token response."""

    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field(default="bearer", description="Token type.")


class ErrorResponse(BaseModel):
    """Standardised error response."""

    detail: str = Field(..., description="Human-readable error message.")
    error_code: str = Field(..., description="Machine-readable error code.")
    timestamp: datetime = Field(
        ..., description="UTC timestamp of when the error occurred."
    )


class AnalysisHistoryItem(BaseModel):
    """Single entry in a user's analysis history."""

    id: str = Field(..., description="Unique analysis identifier.")
    query: str = Field(..., description="Original user query or image reference.")
    diagnosis: str = Field(..., description="Diagnosis result summary.")
    confidence: float = Field(..., description="Confidence score (0.0–1.0).")
    timestamp: datetime = Field(..., description="When the analysis was performed.")


class HistoryResponse(BaseModel):
    """Paginated list of past analyses."""

    items: list[AnalysisHistoryItem] = Field(
        ..., description="Analysis history entries for the current page."
    )
    total: int = Field(..., description="Total number of history entries.")
    page: int = Field(..., description="Current page number.")
    per_page: int = Field(..., description="Number of entries per page.")


class GraphNode(BaseModel):
    """Single node in a knowledge-graph visualisation."""

    id: str = Field(..., description="Unique node identifier.")
    label: str = Field(..., description="Display label for the node.")
    type: str = Field(..., description="Node category (e.g. 'disease', 'crop').")
    properties: dict = Field(
        default_factory=dict, description="Arbitrary key-value metadata."
    )


class GraphEdge(BaseModel):
    """Directed edge between two knowledge-graph nodes."""

    source: str = Field(..., description="Source node identifier.")
    target: str = Field(..., description="Target node identifier.")
    relationship: str = Field(..., description="Relationship type label.")
    weight: float = Field(default=1.0, description="Edge weight or strength.")


class GraphVisualization(BaseModel):
    """Complete knowledge-graph subgraph for frontend rendering."""

    nodes: list[GraphNode] = Field(..., description="Graph nodes.")
    edges: list[GraphEdge] = Field(..., description="Graph edges.")


class CropHealthPredictionResponse(BaseModel):
    """Response model for crop health prediction endpoint."""

    health_status: str = Field(..., description="Predicted crop health status.")
    risk_score: float = Field(..., description="Estimated risk score (0.0-1.0).")
    confidence: float = Field(..., description="Prediction confidence score (0.0-1.0).")
    recommendations: list[str] = Field(..., description="Field recommendations based on prediction.")
    factors: dict[str, float] = Field(..., description="Input factors used for inference.")


class WeatherRecommendationResponse(BaseModel):
    """Response model for weather recommendation endpoint."""

    current_weather: dict[str, float] = Field(..., description="Current weather metrics.")
    recommendations: list[str] = Field(..., description="Weather-driven operational recommendations.")
    irrigation_alert: str = Field(..., description="Irrigation adjustment alert.")


class SoilAnalysisResponse(BaseModel):
    """Response model for soil nutrient analysis endpoint."""

    overall_health: str = Field(..., description="Overall soil health status.")
    nutrient_levels: dict[str, str] = Field(..., description="Classified nutrient levels by parameter.")
    deficiencies: list[str] = Field(..., description="Identified low nutrient categories.")
    recommendations: list[str] = Field(..., description="Recommended soil management actions.")
