"""LangGraph multi-agent orchestrator for the Agricultural AI Platform.

When *langgraph* is installed the orchestrator builds a proper
:class:`StateGraph` with conditional routing.  If the package is
unavailable a lightweight **sequential fallback pipeline** calls the
same node functions in a deterministic order so the platform still
works without the extra dependency.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.orchestrators.workflow_nodes import (
    AgriState,
    decision_node,
    fusion_node,
    graph_rag_node,
    router_node,
    vector_rag_node,
    vision_node,
    voice_node,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional LangGraph import
# ---------------------------------------------------------------------------

try:
    from langgraph.graph import END, StateGraph  # type: ignore[import-untyped]

    _LANGGRAPH_AVAILABLE = True
    logger.debug("langgraph loaded – using graph-based orchestration")
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    logger.info("langgraph not installed – falling back to sequential pipeline")


# ---------------------------------------------------------------------------
# Conditional routing helpers (used by the StateGraph edges)
# ---------------------------------------------------------------------------


def _after_router(state: AgriState) -> list[str]:
    """Return the list of node names that should execute after the router."""
    targets: list[str] = []
    if state.get("_needs_voice"):
        targets.append("voice")
    if state.get("_needs_vision"):
        targets.append("vision")
    targets.append("graph_rag")
    targets.append("vector_rag")
    return targets or ["fusion"]


def _after_parallel(state: AgriState) -> str:
    """Always proceed to the fusion node after parallel branches complete."""
    return "fusion"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def _build_graph():  # noqa: ANN202 – return type depends on optional import
    """Construct the LangGraph ``StateGraph`` (requires *langgraph*)."""
    graph = StateGraph(AgriState)

    # Nodes
    graph.add_node("router", router_node)
    graph.add_node("vision", vision_node)
    graph.add_node("voice", voice_node)
    graph.add_node("graph_rag", graph_rag_node)
    graph.add_node("vector_rag", vector_rag_node)
    graph.add_node("fusion", fusion_node)
    graph.add_node("decision", decision_node)

    # Entry
    graph.set_entry_point("router")

    # Conditional fan-out from router
    graph.add_conditional_edges(
        "router",
        _after_router,
        {
            "vision": "vision",
            "voice": "voice",
            "graph_rag": "graph_rag",
            "vector_rag": "vector_rag",
            "fusion": "fusion",
        },
    )

    # After each parallel branch → fusion
    for node_name in ("vision", "voice", "graph_rag", "vector_rag"):
        graph.add_edge(node_name, "fusion")

    # fusion → decision → END
    graph.add_edge("fusion", "decision")
    graph.add_edge("decision", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Sequential fallback pipeline (no langgraph)
# ---------------------------------------------------------------------------


async def _sequential_pipeline(state: AgriState) -> AgriState:
    """Execute nodes in a deterministic order without LangGraph."""
    state = await router_node(state)

    # Run voice first (may enrich the query)
    if state.get("_needs_voice"):
        state = await voice_node(state)

    # Run vision, graph-RAG, and vector-RAG concurrently
    coros: list = []
    if state.get("_needs_vision"):
        coros.append(vision_node({**state}))
    coros.append(graph_rag_node({**state}))
    coros.append(vector_rag_node({**state}))

    if coros:
        results = await asyncio.gather(*coros, return_exceptions=True)
        for partial in results:
            if isinstance(partial, BaseException):
                state.setdefault("errors", []).append(str(partial))
                continue
            # Merge non-None results back into the canonical state
            for key in (
                "vision_result",
                "graph_rag_result",
                "vector_result",
            ):
                if partial.get(key) is not None:
                    state[key] = partial[key]  # type: ignore[literal-required]
            # Merge errors
            state.setdefault("errors", []).extend(partial.get("errors", []))

    state = await fusion_node(state)
    state = await decision_node(state)
    return state


# ---------------------------------------------------------------------------
# Public orchestrator class
# ---------------------------------------------------------------------------


class AgriOrchestrator:
    """High-level entry point for the multi-agent agricultural AI pipeline.

    Example::

        orchestrator = AgriOrchestrator()
        result = await orchestrator.process(
            query="What disease does this tomato have?",
            image_data=raw_bytes,
            language="en",
        )
    """

    def __init__(self) -> None:
        self._compiled_graph: Any | None = None
        if _LANGGRAPH_AVAILABLE:
            try:
                self._compiled_graph = _build_graph()
                logger.info("AgriOrchestrator initialised with LangGraph")
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "LangGraph graph compilation failed (%s) – using fallback",
                    exc,
                )

    async def process(
        self,
        query: str = "",
        image_data: bytes | None = None,
        audio_data: bytes | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        """Run the full diagnosis pipeline and return the final response dict.

        Parameters
        ----------
        query:
            Free-text question from the user.
        image_data:
            Raw image bytes (JPEG / PNG) or ``None``.
        audio_data:
            Raw audio bytes (WAV / MP3) or ``None``.
        language:
            ISO-639-1 code – ``"en"`` or ``"ar"``.

        Returns
        -------
        dict
            The ``final_response`` produced by the decision node, plus any
            collected errors.
        """
        request_id = uuid.uuid4().hex[:12]
        initial_state: AgriState = {
            "query": query,
            "language": language,
            "image_data": image_data,
            "audio_data": audio_data,
            "vision_result": None,
            "graph_rag_result": None,
            "vector_result": None,
            "voice_result": None,
            "fused_result": None,
            "final_response": None,
            "request_id": request_id,
            "errors": [],
        }

        logger.info("Processing request %s (langgraph=%s)", request_id, _LANGGRAPH_AVAILABLE)

        try:
            if self._compiled_graph is not None:
                final_state = await self._compiled_graph.ainvoke(initial_state)
            else:
                final_state = await _sequential_pipeline(initial_state)
        except Exception as exc:  # noqa: BLE001
            logger.error("Orchestrator error for %s: %s", request_id, exc)
            return {
                "request_id": request_id,
                "errors": [str(exc)],
                "final_response": None,
            }

        return {
            "request_id": request_id,
            **(final_state.get("final_response") or {}),
            "errors": final_state.get("errors", []),
        }
