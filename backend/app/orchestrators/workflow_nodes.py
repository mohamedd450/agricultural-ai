"""Individual node functions for the LangGraph agricultural-AI workflow.

Each node receives the shared :class:`AgriState` dictionary and returns an
updated copy.  Nodes are designed to be composed into a
:class:`langgraph.graph.StateGraph`.
"""

from __future__ import annotations

import logging
from typing import Optional, TypedDict

from app.dependencies import (
    get_decision_router,
    get_fusion_service,
    get_graph_rag_service,
    get_vector_db_service,
    get_vision_service,
    get_voice_service,
)
from app.utils.logger import get_logger

logger: logging.Logger = get_logger(__name__)


# ── Shared workflow state ────────────────────────────────────────────────────


class AgriState(TypedDict, total=False):
    """Typed dictionary that flows through every node in the workflow."""

    input_type: str
    text_query: str
    image_data: Optional[bytes]
    audio_data: Optional[bytes]
    language: str
    session_id: str
    vision_result: Optional[dict]
    voice_result: Optional[dict]
    graph_rag_result: Optional[dict]
    vector_result: Optional[dict]
    routing_decision: Optional[dict]
    fused_result: Optional[dict]
    final_response: Optional[dict]
    error: Optional[str]


# ── Node implementations ─────────────────────────────────────────────────────


async def router_node(state: AgriState) -> AgriState:
    """Detect the input modality from state contents."""
    try:
        if state.get("image_data"):
            input_type = "image"
        elif state.get("audio_data"):
            input_type = "voice"
        else:
            input_type = "text"

        logger.info("Router node: detected input_type=%s", input_type)
        return {**state, "input_type": input_type}
    except Exception as exc:
        logger.error("Router node failed: %s", exc, exc_info=True)
        return {**state, "input_type": "text", "error": str(exc)}


async def vision_node(state: AgriState) -> AgriState:
    """Run image analysis via :class:`VisionService`."""
    image_data = state.get("image_data")
    if not image_data:
        logger.debug("Vision node: no image data – skipping")
        return state

    try:
        vision_service = get_vision_service()
        if not vision_service.is_loaded:
            logger.warning("Vision node: model not loaded")
            return {**state, "vision_result": None}

        result = await vision_service.analyze_image(image_data)
        logger.info(
            "Vision node: class=%s confidence=%.2f",
            result.get("class", "unknown"),
            result.get("confidence", 0.0),
        )
        return {**state, "vision_result": result}
    except Exception as exc:
        logger.error("Vision node failed: %s", exc, exc_info=True)
        return {**state, "vision_result": None, "error": str(exc)}


async def voice_node(state: AgriState) -> AgriState:
    """Transcribe audio via :class:`VoiceService` and populate ``text_query``."""
    audio_data = state.get("audio_data")
    if not audio_data:
        logger.debug("Voice node: no audio data – skipping")
        return state

    try:
        voice_service = get_voice_service()
        if not voice_service.is_loaded:
            logger.warning("Voice node: model not loaded")
            return {**state, "voice_result": None}

        language = state.get("language", "ar")
        result = await voice_service.speech_to_text(audio_data, language=language)
        transcribed_text = result.get("text", "")

        logger.info(
            "Voice node: transcribed %d chars, confidence=%.2f",
            len(transcribed_text),
            result.get("confidence", 0.0),
        )

        updated: AgriState = {**state, "voice_result": result}
        if transcribed_text:
            updated["text_query"] = transcribed_text
        return updated
    except Exception as exc:
        logger.error("Voice node failed: %s", exc, exc_info=True)
        return {**state, "voice_result": None, "error": str(exc)}


async def edgequake_node(state: AgriState) -> AgriState:
    """Query the knowledge graph via :class:`GraphRAGService`."""
    text_query = state.get("text_query", "")
    if not text_query:
        logger.debug("EdgeQuake node: no text query – skipping")
        return state

    try:
        graph_rag = get_graph_rag_service()
        if not graph_rag.is_available:
            logger.warning("EdgeQuake node: service unavailable")
            return {**state, "graph_rag_result": None}

        language = state.get("language", "ar")
        result = await graph_rag.query(text_query, language=language)

        logger.info(
            "EdgeQuake node: confidence=%.2f",
            result.get("confidence", 0.0),
        )
        return {**state, "graph_rag_result": result}
    except Exception as exc:
        logger.error("EdgeQuake node failed: %s", exc, exc_info=True)
        return {**state, "graph_rag_result": None, "error": str(exc)}


async def vector_rag_node(state: AgriState) -> AgriState:
    """Search the vector database via :class:`VectorDBService`."""
    text_query = state.get("text_query", "")
    if not text_query:
        logger.debug("Vector-RAG node: no text query – skipping")
        return state

    try:
        vector_db = get_vector_db_service()
        if not vector_db.is_available:
            logger.warning("Vector-RAG node: service unavailable")
            return {**state, "vector_result": None}

        result = await vector_db.search(text_query)

        logger.info(
            "Vector-RAG node: confidence=%.2f",
            result.get("confidence", 0.0),
        )
        return {**state, "vector_result": result}
    except Exception as exc:
        logger.error("Vector-RAG node failed: %s", exc, exc_info=True)
        return {**state, "vector_result": None, "error": str(exc)}


async def fusion_node(state: AgriState) -> AgriState:
    """Merge all source results via :class:`FusionService`."""
    try:
        fusion_service = get_fusion_service()
        language = state.get("language", "ar")

        result = await fusion_service.fuse(
            vision_result=state.get("vision_result"),
            graph_rag_result=state.get("graph_rag_result"),
            vector_result=state.get("vector_result"),
            routing_decision=state.get("routing_decision"),
            language=language,
        )

        logger.info(
            "Fusion node: confidence=%.2f source=%s",
            result.get("confidence", 0.0),
            result.get("source", "unknown"),
        )
        return {**state, "fused_result": result, "final_response": result}
    except Exception as exc:
        logger.error("Fusion node failed: %s", exc, exc_info=True)
        return {**state, "fused_result": None, "error": str(exc)}


async def decision_node(state: AgriState) -> AgriState:
    """Route results via :class:`DecisionRouter`, then fuse based on decision."""
    try:
        router = get_decision_router()
        has_image = bool(state.get("image_data"))

        routing = await router.route(
            vision_result=state.get("vision_result"),
            graph_rag_result=state.get("graph_rag_result"),
            vector_result=state.get("vector_result"),
            has_image=has_image,
        )

        logger.info(
            "Decision node: strategy=%s primary=%s confidence=%.2f",
            routing.get("strategy", "unknown"),
            routing.get("primary_source", "unknown"),
            routing.get("confidence", 0.0),
        )

        fusion_service = get_fusion_service()
        language = state.get("language", "ar")

        fused = await fusion_service.fuse(
            vision_result=state.get("vision_result"),
            graph_rag_result=state.get("graph_rag_result"),
            vector_result=state.get("vector_result"),
            routing_decision=routing,
            language=language,
        )

        return {
            **state,
            "routing_decision": routing,
            "fused_result": fused,
            "final_response": fused,
        }
    except Exception as exc:
        logger.error("Decision node failed: %s", exc, exc_info=True)
        return {**state, "routing_decision": None, "error": str(exc)}


# ── Conditional edge helpers ─────────────────────────────────────────────────


def should_process_image(state: AgriState) -> str:
    """Return ``'vision'`` when image data is present, else ``'skip_vision'``."""
    return "vision" if state.get("image_data") else "skip_vision"


def should_process_voice(state: AgriState) -> str:
    """Return ``'voice'`` when audio data is present, else ``'skip_voice'``."""
    return "voice" if state.get("audio_data") else "skip_voice"
