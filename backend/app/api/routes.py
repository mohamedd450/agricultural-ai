"""Main API v1 endpoints for the Agricultural AI Platform.

Covers multimodal analysis, voice processing, text queries,
analysis history, and user feedback submission.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.security import TokenData, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class AnalysisResponse(BaseModel):
    """Response for multimodal / text analysis."""

    request_id: str
    diagnosis: str
    confidence: float
    graph_paths: List[str] = []
    explanation: str


class VoiceResponse(BaseModel):
    """Response for voice analysis."""

    request_id: str
    transcription: str
    diagnosis: str
    audio_url: Optional[str] = None


class TextRequest(BaseModel):
    """Body for text-only queries."""

    query: str
    language: str = "ar"


class FeedbackRequest(BaseModel):
    """Body for submitting feedback on an analysis."""

    request_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Acknowledgement of submitted feedback."""

    status: str
    request_id: str


class HistoryItem(BaseModel):
    """Single item in the analysis history."""

    request_id: str
    diagnosis: str
    confidence: float
    created_at: str


# ---------------------------------------------------------------------------
# POST /api/v1/analyze — multimodal analysis
# ---------------------------------------------------------------------------
@router.post("/analyze", response_model=AnalysisResponse, summary="Multimodal analysis")
async def analyze(
    image: UploadFile = File(...),
    text: Optional[str] = Form(None),
    language: str = Form("ar"),
    settings: Settings = Depends(get_settings),
) -> AnalysisResponse:
    """Accept an image (and optional text / language) and return a diagnosis.

    The endpoint delegates to the orchestrator layer for actual inference.
    """
    request_id = str(uuid.uuid4())
    logger.info("Analyze request %s – language=%s, has_text=%s", request_id, language, text is not None)

    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image is empty.",
            )

        # TODO: delegate to orchestrator for real inference
        return AnalysisResponse(
            request_id=request_id,
            diagnosis="Healthy crop detected",
            confidence=0.92,
            graph_paths=[],
            explanation="No disease symptoms found in the submitted image.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analysis failed for request %s", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# POST /api/v1/voice — voice analysis
# ---------------------------------------------------------------------------
@router.post("/voice", response_model=VoiceResponse, summary="Voice analysis")
async def voice_analysis(
    audio: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> VoiceResponse:
    """Accept an audio file, transcribe it, and return a diagnosis."""
    request_id = str(uuid.uuid4())
    logger.info("Voice request %s – filename=%s", request_id, audio.filename)

    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio is empty.",
            )

        # TODO: delegate to whisper transcription + orchestrator
        return VoiceResponse(
            request_id=request_id,
            transcription="Sample transcription",
            diagnosis="Pest infestation suspected",
            audio_url=None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Voice analysis failed for request %s", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice analysis failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# POST /api/v1/text — text-only query
# ---------------------------------------------------------------------------
@router.post("/text", response_model=AnalysisResponse, summary="Text-only query")
async def text_query(body: TextRequest) -> AnalysisResponse:
    """Process a text-only agricultural query and return a diagnosis."""
    request_id = str(uuid.uuid4())
    logger.info("Text query %s – language=%s", request_id, body.language)

    try:
        # TODO: delegate to orchestrator for real inference
        return AnalysisResponse(
            request_id=request_id,
            diagnosis="Nutrient deficiency detected",
            confidence=0.85,
            graph_paths=[],
            explanation=f"Based on your description: '{body.query}'",
        )
    except Exception as exc:
        logger.exception("Text query failed for request %s", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text query failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# GET /api/v1/history — analysis history (auth required)
# ---------------------------------------------------------------------------
@router.get("/history", response_model=List[HistoryItem], summary="Analysis history")
async def analysis_history(
    current_user: TokenData = Depends(get_current_user),
) -> List[HistoryItem]:
    """Return the authenticated user's previous analysis history."""
    logger.info("History request from user=%s", current_user.sub)

    # TODO: fetch from database
    return []


# ---------------------------------------------------------------------------
# POST /api/v1/feedback — submit feedback
# ---------------------------------------------------------------------------
@router.post("/feedback", response_model=FeedbackResponse, summary="Submit feedback")
async def submit_feedback(body: FeedbackRequest) -> FeedbackResponse:
    """Submit user feedback for a previous analysis."""
    logger.info(
        "Feedback for request %s – rating=%d, comment=%s",
        body.request_id,
        body.rating,
        body.comment,
    )

    # TODO: persist feedback
    return FeedbackResponse(status="received", request_id=body.request_id)
