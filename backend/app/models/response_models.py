"""Pydantic response models for the Agricultural AI platform."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DiagnosisResponse(BaseModel):
    """Response model for crop disease diagnosis."""

    diagnosis: str = Field(..., description="Identified disease or condition")
    treatment: str = Field(..., description="Recommended treatment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    graph_paths: list[str] = Field(
        default_factory=list, description="Knowledge graph paths used for reasoning"
    )
    explanation: str = Field(..., description="Human-readable explanation of the diagnosis")
    language: str = Field(..., description="Language of the response")
    request_id: str = Field(..., description="Request tracking ID")
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    sources: list[str] = Field(
        default_factory=list, description="References and data sources used"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "diagnosis": "Early Blight (Alternaria solani)",
                    "treatment": "Apply chlorothalonil fungicide. Remove affected leaves.",
                    "confidence": 0.92,
                    "graph_paths": [
                        "Tomato -> susceptible_to -> Early Blight",
                        "Early Blight -> treated_by -> Chlorothalonil",
                    ],
                    "explanation": "Dark concentric rings on lower leaves indicate early blight.",
                    "language": "en",
                    "request_id": "req-abc-123",
                    "processing_time": 1.23,
                    "sources": ["PlantVillage Dataset", "CABI Crop Protection Compendium"],
                }
            ]
        }
    )


class VoiceResponse(BaseModel):
    """Response model for voice-based interactions."""

    text_response: str = Field(..., description="Text version of the response")
    audio_url: Optional[str] = Field(None, description="URL to synthesized audio response")
    language: str = Field(..., description="Language of the response")
    request_id: str = Field(..., description="Request tracking ID")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text_response": "Your wheat crop appears to have rust disease.",
                    "audio_url": "https://api.example.com/audio/resp-456.mp3",
                    "language": "ar",
                    "request_id": "req-voice-789",
                }
            ]
        }
    )


class HealthResponse(BaseModel):
    """Response model for service health checks."""

    status: str = Field(..., description="Overall service status")
    version: str = Field(..., description="API version string")
    uptime: float = Field(..., ge=0.0, description="Service uptime in seconds")
    services: dict[str, str] = Field(
        default_factory=dict, description="Status of downstream services"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "healthy",
                    "version": "1.0.0",
                    "uptime": 3600.5,
                    "services": {
                        "database": "connected",
                        "graph_db": "connected",
                        "ml_model": "loaded",
                    },
                }
            ]
        }
    )


class HistoryItem(BaseModel):
    """Single item in a diagnosis history listing."""

    request_id: str = Field(..., description="Original request tracking ID")
    query: str = Field(..., description="User's original query")
    diagnosis: str = Field(..., description="Returned diagnosis")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the request")
    language: str = Field(..., description="Language of the interaction")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request_id": "req-abc-123",
                    "query": "Yellow spots on tomato leaves",
                    "diagnosis": "Early Blight",
                    "confidence": 0.92,
                    "timestamp": "2025-01-15T10:30:00Z",
                    "language": "en",
                }
            ]
        }
    )


class HistoryResponse(BaseModel):
    """Paginated list of diagnosis history items."""

    items: list[HistoryItem] = Field(default_factory=list, description="History entries")
    total: int = Field(..., ge=0, description="Total number of matching items")
    page: int = Field(..., ge=1, description="Current page number")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "request_id": "req-abc-123",
                            "query": "Yellow spots on tomato leaves",
                            "diagnosis": "Early Blight",
                            "confidence": 0.92,
                            "timestamp": "2025-01-15T10:30:00Z",
                            "language": "en",
                        }
                    ],
                    "total": 42,
                    "page": 1,
                }
            ]
        }
    )


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    status: str = Field(..., description="Feedback processing status")
    message: str = Field(..., description="Human-readable result message")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "accepted",
                    "message": "Thank you for your feedback.",
                }
            ]
        }
    )


class TokenResponse(BaseModel):
    """Response containing an authentication token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type (e.g. 'bearer')")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                }
            ]
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: str = Field(..., description="Error category or code")
    detail: str = Field(..., description="Human-readable error detail")
    request_id: Optional[str] = Field(None, description="Request ID if available")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "ValidationError",
                    "detail": "Field 'query' is required.",
                    "request_id": "req-abc-123",
                }
            ]
        }
    )
