"""Core API routes for the Agricultural AI platform.

All endpoints live under ``/api/v1`` and delegate heavy lifting to injected
service singletons provided by :mod:`app.dependencies`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.dependencies import (
    get_cache_service,
    get_decision_router,
    get_fusion_service,
    get_graph_rag_service,
    get_vector_db_service,
    get_vision_service,
    get_voice_service,
)
from app.models.request_models import FeedbackRequest, LoginRequest, TextQuery
from app.models.response_models import (
    DiagnosisResponse,
    HistoryResponse,
    TokenResponse,
    VoiceResponse,
)
from app.security import create_access_token, verify_password
from app.services.cache_service import CacheService
from app.services.decision_router import DecisionRouter
from app.services.fusion_service import FusionService
from app.services.graph_rag_service import GraphRAGService
from app.services.vector_db_service import VectorDBService
from app.services.vision_service import VisionService
from app.services.voice_service import VoiceService
from app.utils.exceptions import AuthenticationError, InvalidInputError
from app.utils.logger import get_logger
from app.utils.validators import validate_audio, validate_image, validate_language, validate_query

logger: logging.Logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agricultural-ai"])

# ── POST /analyze ────────────────────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=DiagnosisResponse,
    summary="Analyse a crop image",
    description=(
        "Upload a crop image and optionally provide a text description of "
        "symptoms. The platform runs vision analysis, graph-RAG retrieval, "
        "and vector search, then fuses the results into a single diagnosis."
    ),
)
async def analyze(
    image: UploadFile = File(...),
    text_query: str = Form(default=""),
    language: str = Form(default="ar"),
    vision: VisionService = Depends(get_vision_service),
    graph_rag: GraphRAGService = Depends(get_graph_rag_service),
    vector_db: VectorDBService = Depends(get_vector_db_service),
    decision: DecisionRouter = Depends(get_decision_router),
    fusion: FusionService = Depends(get_fusion_service),
    cache: CacheService = Depends(get_cache_service),
) -> DiagnosisResponse:
    language = validate_language(language)
    await validate_image(image)

    image_data = await image.read()
    logger.info("Analyse request: file=%s size=%d language=%s", image.filename, len(image_data), language)

    cache_key = cache.generate_cache_key("analyze", image_size=len(image_data), text_query=text_query, language=language)
    cached = await cache.get_json(cache_key)
    if cached:
        logger.info("Cache hit for analysis %s", cache_key)
        return DiagnosisResponse(**cached)

    vision_result = await vision.analyze_image(image_data) if vision.is_loaded else None
    graph_rag_result = await graph_rag.query(text_query, language=language) if text_query and graph_rag.is_available else None
    vector_result = await vector_db.search(text_query) if text_query and vector_db.is_available else None

    routing = await decision.route(
        vision_result=vision_result,
        graph_rag_result=graph_rag_result,
        vector_result=vector_result,
        has_image=True,
    )

    fused = await fusion.fuse(
        vision_result=vision_result,
        graph_rag_result=graph_rag_result,
        vector_result=vector_result,
        routing_decision=routing,
        language=language,
    )

    response = DiagnosisResponse(**fused)
    await cache.set_json(cache_key, response.model_dump(mode="json"), ttl=3600)
    logger.info("Analysis complete: diagnosis=%s confidence=%.2f", response.diagnosis, response.confidence)
    return response


# ── POST /voice ──────────────────────────────────────────────────────────────


@router.post(
    "/voice",
    response_model=VoiceResponse,
    summary="Voice-based agricultural query",
    description=(
        "Upload an audio recording of a spoken question about crop health. "
        "The platform transcribes the audio, processes the query, and returns "
        "a textual (and optionally audio) response."
    ),
)
async def voice(
    audio: UploadFile = File(...),
    language: str = Form(default="ar"),
    voice_svc: VoiceService = Depends(get_voice_service),
    graph_rag: GraphRAGService = Depends(get_graph_rag_service),
    vector_db: VectorDBService = Depends(get_vector_db_service),
    decision: DecisionRouter = Depends(get_decision_router),
    fusion: FusionService = Depends(get_fusion_service),
) -> VoiceResponse:
    language = validate_language(language)
    await validate_audio(audio)

    audio_data = await audio.read()
    logger.info("Voice request: file=%s size=%d language=%s", audio.filename, len(audio_data), language)

    transcription = await voice_svc.speech_to_text(audio_data, language=language)
    text = transcription.get("text", "")
    if not text:
        raise InvalidInputError(
            message="Could not transcribe audio. Please try again with clearer audio.",
            error_code="TRANSCRIPTION_FAILED",
        )

    logger.info("Transcribed text: %s", text[:100])

    graph_rag_result = await graph_rag.query(text, language=language) if graph_rag.is_available else None
    vector_result = await vector_db.search(text) if vector_db.is_available else None

    routing = await decision.route(
        graph_rag_result=graph_rag_result,
        vector_result=vector_result,
        has_image=False,
    )

    fused = await fusion.fuse(
        graph_rag_result=graph_rag_result,
        vector_result=vector_result,
        routing_decision=routing,
        language=language,
    )

    diagnosis = DiagnosisResponse(**fused)
    text_response = fused.get("explanation", diagnosis.diagnosis)

    return VoiceResponse(
        text_response=text_response,
        audio_url=None,
        diagnosis=diagnosis,
    )


# ── POST /text-query ─────────────────────────────────────────────────────────


@router.post(
    "/text-query",
    response_model=DiagnosisResponse,
    summary="Text-based agricultural query",
    description=(
        "Submit a text description of crop symptoms or an agricultural "
        "question. The platform queries the knowledge graph and vector "
        "database to produce a diagnosis."
    ),
)
async def text_query(
    body: TextQuery,
    graph_rag: GraphRAGService = Depends(get_graph_rag_service),
    vector_db: VectorDBService = Depends(get_vector_db_service),
    decision: DecisionRouter = Depends(get_decision_router),
    fusion: FusionService = Depends(get_fusion_service),
    cache: CacheService = Depends(get_cache_service),
) -> DiagnosisResponse:
    query_text = validate_query(body.query)
    language = validate_language(body.language)

    logger.info("Text query: %s language=%s", query_text[:80], language)

    cache_key = cache.generate_cache_key("text_query", query=query_text, language=language)
    cached = await cache.get_json(cache_key)
    if cached:
        logger.info("Cache hit for text query %s", cache_key)
        return DiagnosisResponse(**cached)

    graph_rag_result = await graph_rag.query(query_text, language=language) if graph_rag.is_available else None
    vector_result = await vector_db.search(query_text) if vector_db.is_available else None

    routing = await decision.route(
        graph_rag_result=graph_rag_result,
        vector_result=vector_result,
        has_image=False,
    )

    fused = await fusion.fuse(
        graph_rag_result=graph_rag_result,
        vector_result=vector_result,
        routing_decision=routing,
        language=language,
    )

    response = DiagnosisResponse(**fused)
    await cache.set_json(cache_key, response.model_dump(mode="json"), ttl=3600)
    logger.info("Text query complete: diagnosis=%s confidence=%.2f", response.diagnosis, response.confidence)
    return response


# ── GET /history ─────────────────────────────────────────────────────────────


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Retrieve analysis history",
    description="Return a paginated list of past analyses for the current user. Currently returns an empty placeholder.",
)
async def history() -> HistoryResponse:
    logger.info("History request (placeholder)")
    return HistoryResponse(items=[], total=0, page=1, per_page=20)


# ── POST /feedback ───────────────────────────────────────────────────────────


@router.post(
    "/feedback",
    summary="Submit analysis feedback",
    description="Allow users to rate and comment on a previous analysis result.",
)
async def feedback(body: FeedbackRequest) -> dict[str, str]:
    logger.info(
        "Feedback received: analysis_id=%s rating=%d comment=%s",
        body.analysis_id,
        body.rating,
        body.comment[:50] if body.comment else None,
    )
    return {"message": "Feedback submitted successfully."}


# ── POST /auth/login ─────────────────────────────────────────────────────────

# Placeholder user store – replace with a real database lookup.
_DEMO_USERS: dict[str, str] = {}


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain a JWT",
    description=(
        "Submit username and password credentials. On success, returns a "
        "signed JWT access token that can be used as a Bearer token for "
        "protected endpoints."
    ),
)
async def login(body: LoginRequest) -> TokenResponse:
    logger.info("Login attempt: user=%s", body.username)

    hashed = _DEMO_USERS.get(body.username)
    if hashed is None or not verify_password(body.password, hashed):
        raise AuthenticationError(
            message="Invalid username or password.",
            error_code="INVALID_CREDENTIALS",
        )

    token = create_access_token(data={"sub": body.username})
    logger.info("Login successful: user=%s", body.username)
    return TokenResponse(access_token=token)
