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


class CropHealthPredictionRequest(BaseModel):
    """Request model for structured crop health prediction."""

    soil_moisture: float = Field(..., ge=0, le=100, description="Soil moisture percentage.")
    temperature_c: float = Field(..., ge=-20, le=70, description="Current field temperature in Celsius.")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity percentage.")
    rainfall_mm_7d: float = Field(..., ge=0, description="Accumulated rainfall in millimeters over the last 7 days.")
    leaf_discoloration: float = Field(..., ge=0, le=1, description="Leaf discoloration severity score (0-1).")
    pest_activity: float = Field(..., ge=0, le=1, description="Pest activity severity score (0-1).")


class WeatherRecommendationRequest(BaseModel):
    """Request model for weather-aware recommendations."""

    latitude: float = Field(..., ge=-90, le=90, description="Farm latitude.")
    longitude: float = Field(..., ge=-180, le=180, description="Farm longitude.")
    crop_type: Optional[str] = Field(default=None, description="Optional crop type for targeted guidance.")


class SoilAnalysisRequest(BaseModel):
    """Request model for soil nutrient analysis."""

    nitrogen: float = Field(..., ge=0, description="Soil nitrogen level.")
    phosphorus: float = Field(..., ge=0, description="Soil phosphorus level.")
    potassium: float = Field(..., ge=0, description="Soil potassium level.")
    ph: float = Field(..., ge=0, le=14, description="Soil pH level.")
    moisture: float = Field(..., ge=0, le=100, description="Soil moisture percentage.")
