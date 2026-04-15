"""Request models for the Agricultural AI platform API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request model for crop disease analysis."""

    image: Optional[str] = Field(
        default=None,
        description="Base64-encoded image data. The actual UploadFile is handled at the route level.",
    )
    text_query: Optional[str] = Field(
        default=None,
        description="Optional text description of the observed symptoms.",
    )
    language: Literal["ar", "en"] = Field(
        default="ar",
        description="Response language: 'ar' for Arabic, 'en' for English.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation continuity.",
    )


class VoiceRequest(BaseModel):
    """Request model for voice-based interaction. Audio file is received as UploadFile in the route."""

    language: Literal["ar", "en"] = Field(
        default="ar",
        description="Language of the voice input: 'ar' for Arabic, 'en' for English.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation continuity.",
    )


class TextQuery(BaseModel):
    """Request model for text-based agricultural queries."""

    query: str = Field(
        ...,
        description="The agricultural question or symptom description.",
    )
    language: Literal["ar", "en"] = Field(
        default="ar",
        description="Response language: 'ar' for Arabic, 'en' for English.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation continuity.",
    )


class LoginRequest(BaseModel):
    """Request model for user authentication."""

    username: str = Field(..., description="Account username.")
    password: str = Field(..., description="Account password.")


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback on an analysis."""

    analysis_id: str = Field(..., description="Identifier of the analysis being rated.")
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 (poor) to 5 (excellent).",
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional free-text comment.",
    )
