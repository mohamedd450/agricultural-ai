"""Pydantic models for the Agricultural AI platform."""

from .graph_models import (
    GraphEdge,
    GraphNode,
    GraphPath,
    GraphRAGResponse,
    KnowledgeSubgraph,
)
from .request_models import (
    AnalysisRequest,
    FeedbackRequest,
    TextQueryRequest,
    UserLoginRequest,
    UserRegisterRequest,
    VoiceRequest,
)
from .response_models import (
    DiagnosisResponse,
    ErrorResponse,
    FeedbackResponse,
    HealthResponse,
    HistoryItem,
    HistoryResponse,
    TokenResponse,
    VoiceResponse,
)

__all__ = [
    # Request models
    "AnalysisRequest",
    "FeedbackRequest",
    "TextQueryRequest",
    "UserLoginRequest",
    "UserRegisterRequest",
    "VoiceRequest",
    # Response models
    "DiagnosisResponse",
    "ErrorResponse",
    "FeedbackResponse",
    "HealthResponse",
    "HistoryItem",
    "HistoryResponse",
    "TokenResponse",
    "VoiceResponse",
    # Graph models
    "GraphEdge",
    "GraphNode",
    "GraphPath",
    "GraphRAGResponse",
    "KnowledgeSubgraph",
]
