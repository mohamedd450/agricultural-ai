"""Individual LangGraph node functions for the agricultural AI workflow.

Each node receives the shared ``AgriState`` TypedDict, performs its work,
and returns an updated copy.  All functions are *async* and catch their own
errors so that a single failing service never crashes the whole pipeline.
"""

from __future__ import annotations

import traceback
from typing import Any, TypedDict

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared state definition
# ---------------------------------------------------------------------------

class AgriState(TypedDict, total=False):
    """Mutable state dict threaded through every graph node."""

    query: str
    language: str
    image_data: bytes | None
    audio_data: bytes | None
    vision_result: dict[str, Any] | None
    graph_rag_result: dict[str, Any] | None
    vector_result: dict[str, Any] | None
    voice_result: dict[str, Any] | None
    fused_result: dict[str, Any] | None
    final_response: dict[str, Any] | None
    request_id: str
    errors: list[str]


def _ensure_errors(state: AgriState) -> list[str]:
    """Return the existing error list or create one."""
    if "errors" not in state or state["errors"] is None:
        state["errors"] = []
    return state["errors"]


# ---------------------------------------------------------------------------
# Router node
# ---------------------------------------------------------------------------

async def router_node(state: AgriState) -> AgriState:
    """Determine which downstream services should be called.

    Sets boolean-style keys so conditional edges can inspect the state later:
    ``_needs_vision``, ``_needs_voice``, ``_needs_graph_rag``,
    ``_needs_vector_rag``.
    """
    _ensure_errors(state)
    try:
        state["_needs_vision"] = state.get("image_data") is not None  # type: ignore[typeddict-unknown-key]
        state["_needs_voice"] = state.get("audio_data") is not None  # type: ignore[typeddict-unknown-key]
        state["_needs_graph_rag"] = True  # type: ignore[typeddict-unknown-key]
        state["_needs_vector_rag"] = True  # type: ignore[typeddict-unknown-key]

        logger.info(
            "[router] vision=%s  voice=%s  graph_rag=True  vector_rag=True",
            state.get("_needs_vision"),
            state.get("_needs_voice"),
        )
    except Exception as exc:  # noqa: BLE001
        state["errors"].append(f"router_node: {exc}")
        logger.error("router_node failed: %s", traceback.format_exc())
    return state


# ---------------------------------------------------------------------------
# Vision node
# ---------------------------------------------------------------------------

async def vision_node(state: AgriState) -> AgriState:
    """Analyse an image through :class:`VisionService`."""
    _ensure_errors(state)
    if not state.get("image_data"):
        return state
    try:
        from app.services import VisionService

        svc = VisionService()
        result = await svc.analyze_image(state["image_data"])
        state["vision_result"] = result
        logger.info("[vision] analysis complete")
    except Exception as exc:  # noqa: BLE001
        state["errors"].append(f"vision_node: {exc}")
        logger.error("vision_node failed: %s", traceback.format_exc())
    return state


# ---------------------------------------------------------------------------
# Voice node
# ---------------------------------------------------------------------------

async def voice_node(state: AgriState) -> AgriState:
    """Transcribe audio via :class:`VoiceService`."""
    _ensure_errors(state)
    if not state.get("audio_data"):
        return state
    try:
        from app.services import VoiceService

        svc = VoiceService()
        language = state.get("language", "ar")
        result = await svc.speech_to_text(state["audio_data"], language=language)
        state["voice_result"] = result
        # Append transcription to query – result may be a str or a dict
        transcribed_text = result.get("text") if isinstance(result, dict) else result
        if transcribed_text:
            existing = state.get("query", "")
            state["query"] = f"{existing} {transcribed_text}".strip()
        logger.info("[voice] transcription complete")
    except Exception as exc:  # noqa: BLE001
        state["errors"].append(f"voice_node: {exc}")
        logger.error("voice_node failed: %s", traceback.format_exc())
    return state


# ---------------------------------------------------------------------------
# Graph-RAG node
# ---------------------------------------------------------------------------

async def graph_rag_node(state: AgriState) -> AgriState:
    """Query the knowledge graph via :class:`GraphRAGService`."""
    _ensure_errors(state)
    query = state.get("query", "")
    if not query:
        return state
    try:
        from app.services import GraphRAGService

        svc = GraphRAGService()
        language = state.get("language", "en")
        result = await svc.query(
            question=query,
            context=state.get("vision_result"),
            language=language,
        )
        state["graph_rag_result"] = result
        logger.info("[graph_rag] query complete")
    except Exception as exc:  # noqa: BLE001
        state["errors"].append(f"graph_rag_node: {exc}")
        logger.error("graph_rag_node failed: %s", traceback.format_exc())
    return state


# ---------------------------------------------------------------------------
# Vector-RAG node
# ---------------------------------------------------------------------------

async def vector_rag_node(state: AgriState) -> AgriState:
    """Semantic search through :class:`VectorDBService`."""
    _ensure_errors(state)
    query = state.get("query", "")
    if not query:
        return state
    try:
        from app.services import VectorDBService

        svc = VectorDBService()
        language = state.get("language", "en")
        result = await svc.search(query=query, language=language)
        state["vector_result"] = result
        logger.info("[vector_rag] search complete")
    except Exception as exc:  # noqa: BLE001
        state["errors"].append(f"vector_rag_node: {exc}")
        logger.error("vector_rag_node failed: %s", traceback.format_exc())
    return state


# ---------------------------------------------------------------------------
# Fusion node
# ---------------------------------------------------------------------------

async def fusion_node(state: AgriState) -> AgriState:
    """Fuse multi-source results via :class:`FusionService`."""
    _ensure_errors(state)
    try:
        from app.services import FusionService

        svc = FusionService()
        fused = await svc.fuse(
            vision_output=state.get("vision_result"),
            graph_rag_output=state.get("graph_rag_result"),
            vector_output=state.get("vector_result"),
            user_context={"query": state.get("query", "")},
        )
        state["fused_result"] = fused
        logger.info("[fusion] results fused")
    except Exception as exc:  # noqa: BLE001
        state["errors"].append(f"fusion_node: {exc}")
        logger.error("fusion_node failed: %s", traceback.format_exc())
    return state


# ---------------------------------------------------------------------------
# Decision node
# ---------------------------------------------------------------------------

async def decision_node(state: AgriState) -> AgriState:
    """Route fused results through :class:`DecisionRouter` and build the final response."""
    _ensure_errors(state)
    try:
        from app.services import DecisionRouter

        router = DecisionRouter()
        decision = router.route(
            vision_result=state.get("vision_result"),
            graph_rag_result=state.get("graph_rag_result"),
            vector_result=state.get("vector_result"),
        )

        state["final_response"] = {
            "diagnosis": state.get("fused_result"),
            "decision": decision,
            "query": state.get("query", ""),
            "language": state.get("language", "en"),
            "errors": state.get("errors", []),
        }
        logger.info("[decision] final response built")
    except Exception as exc:  # noqa: BLE001
        state["errors"].append(f"decision_node: {exc}")
        logger.error("decision_node failed: %s", traceback.format_exc())
        # Provide a degraded response rather than nothing
        state["final_response"] = {
            "diagnosis": state.get("fused_result") or state.get("vision_result"),
            "decision": None,
            "query": state.get("query", ""),
            "language": state.get("language", "en"),
            "errors": state.get("errors", []),
        }
    return state
