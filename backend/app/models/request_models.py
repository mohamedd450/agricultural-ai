"""Pydantic request models for the Agricultural AI platform."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalysisRequest(BaseModel):
    """Request model for crop disease analysis."""

    text: Optional[str] = Field(None, description="Text description of the crop issue")
    language: str = Field("en", description="ISO 639-1 language code")
    image_data: Optional[bytes] = Field(None, description="Raw image bytes for visual analysis")
    request_id: Optional[str] = Field(None, description="Client-provided request tracking ID")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 5:
            raise ValueError("Language code must be 2-5 characters (e.g. 'en', 'ar', 'en-US')")
        return v.lower()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "My tomato leaves have yellow spots",
                    "language": "en",
                    "request_id": "req-abc-123",
                }
            ]
        }
    )


class VoiceRequest(BaseModel):
    """Request model for voice-based queries."""

    language: str = Field("ar", description="ISO 639-1 language code for speech recognition")
    audio_data: Optional[bytes] = Field(None, description="Raw audio bytes")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 5:
            raise ValueError("Language code must be 2-5 characters")
        return v.lower()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "language": "ar",
                }
            ]
        }
    )


class TextQueryRequest(BaseModel):
    """Request model for text-based knowledge queries."""

    query: str = Field(..., min_length=1, description="The user's question about agriculture")
    language: str = Field("en", description="ISO 639-1 language code")
    use_graph_rag: bool = Field(True, description="Whether to use Graph RAG for retrieval")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 5:
            raise ValueError("Language code must be 2-5 characters")
        return v.lower()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "What causes early blight in potatoes?",
                    "language": "en",
                    "use_graph_rag": True,
                }
            ]
        }
    )


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback on a diagnosis."""

    request_id: str = Field(..., description="ID of the original diagnosis request")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    comment: Optional[str] = Field(None, description="Optional free-text comment")
    correct_diagnosis: Optional[str] = Field(
        None, description="User-provided correct diagnosis if the system was wrong"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request_id": "req-abc-123",
                    "rating": 4,
                    "comment": "Diagnosis was accurate",
                    "correct_diagnosis": None,
                }
            ]
        }
    )


class UserLoginRequest(BaseModel):
    """Request model for user authentication."""

    username: str = Field(..., min_length=1, description="Account username")
    password: str = Field(..., min_length=1, description="Account password")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "username": "farmer_ali",
                    "password": "securepassword123",
                }
            ]
        }
    )


class UserRegisterRequest(BaseModel):
    """Request model for new user registration."""

    username: str = Field(..., min_length=3, description="Desired username")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    email: str = Field(..., description="Email address")
    preferred_language: str = Field("en", description="Preferred UI language")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address format")
        return v

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 5:
            raise ValueError("Language code must be 2-5 characters")
        return v.lower()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "username": "farmer_ali",
                    "password": "securepassword123",
                    "email": "ali@example.com",
                    "preferred_language": "ar",
                }
            ]
        }
    )
