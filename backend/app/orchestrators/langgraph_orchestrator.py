"""LangGraph-based workflow orchestrator for the Agricultural AI platform.

Builds a :class:`StateGraph` that routes inputs through vision, voice,
graph-RAG, vector-RAG, and fusion nodes.  Falls back to a simple sequential
pipeline when LangGraph is not installed.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.dependencies import (
    get_decision_router,
    get_fusion_service,
    get_graph_rag_service,
    get_vector_db_service,
    get_vision_service,
    get_voice_service,
)
from app.orchestrators.workflow_nodes import (
    AgriState,
    decision_node,
    edgequake_node,
    fusion_node,
    router_node,
    should_process_image,
    should_process_voice,
    vector_rag_node,
    vision_node,
    voice_node,
)
from app.utils.logger import get_logger

logger: logging.Logger = get_logger(__name__)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover
    LANGGRAPH_AVAILABLE = False
    logger.warning(
        "langgraph not installed – using sequential fallback orchestrator"
    )


class LangGraphOrchestrator:
    """Orchestrate the multi-agent agricultural-AI workflow.

    When LangGraph is available the orchestrator compiles a full
    :class:`StateGraph`.  Otherwise it falls back to
    :meth:`_simple_sequential_process`.
    """

    def __init__(self) -> None:
        self._workflow: Optional[Any] = None
        if LANGGRAPH_AVAILABLE:
            try:
                self._workflow = self._build_workflow()
                logger.info("LangGraph workflow compiled successfully")
            except Exception:
                logger.error(
                    "Failed to build LangGraph workflow – using fallback",
                    exc_info=True,
                )
                self._workflow = None
        else:
            logger.info("LangGraph unavailable – sequential fallback active")

    # ── Workflow construction ────────────────────────────────────────────

    def _build_workflow(self) -> Any:
        """Construct and compile the :class:`StateGraph`.

        Graph topology::

            START → router
            router ─┬─ (image)  → vision_agent  → edgequake_agent
                    ├─ (voice)  → voice_agent   → edgequake_agent
                    └─ (text)   → edgequake_agent
            edgequake_agent → vector_rag_agent → fusion_agent
            fusion_agent → decision_agent → END
        """
        graph = StateGraph(AgriState)

        # Register nodes
        graph.add_node("router", router_node)
        graph.add_node("vision_agent", vision_node)
        graph.add_node("voice_agent", voice_node)
        graph.add_node("edgequake_agent", edgequake_node)
        graph.add_node("vector_rag_agent", vector_rag_node)
        graph.add_node("fusion_agent", fusion_node)
        graph.add_node("decision_agent", decision_node)

        # Entry point
        graph.set_entry_point("router")

        # Conditional edges from router
        graph.add_conditional_edges(
            "router",
            self._route_by_input_type,
            {
                "vision_agent": "vision_agent",
                "voice_agent": "voice_agent",
                "edgequake_agent": "edgequake_agent",
            },
        )

        # After vision / voice → continue to edgequake
        graph.add_edge("vision_agent", "edgequake_agent")
        graph.add_edge("voice_agent", "edgequake_agent")

        # Linear tail
        graph.add_edge("edgequake_agent", "vector_rag_agent")
        graph.add_edge("vector_rag_agent", "fusion_agent")
        graph.add_edge("fusion_agent", "decision_agent")
        graph.add_edge("decision_agent", END)

        return graph.compile()

    # ── Conditional routing helper ───────────────────────────────────────

    @staticmethod
    def _route_by_input_type(state: AgriState) -> str:
        """Return the next node name based on detected ``input_type``."""
        input_type = state.get("input_type", "text")
        if input_type == "image":
            return "vision_agent"
        if input_type == "voice":
            return "voice_agent"
        return "edgequake_agent"

    # ── Public API ───────────────────────────────────────────────────────

    async def process(self, input_data: dict) -> dict:
        """Run the workflow and return the final response.

        Parameters
        ----------
        input_data:
            Initial :class:`AgriState` fields (at minimum ``text_query``
            or ``image_data`` or ``audio_data``).

        Returns
        -------
        dict
            The ``final_response`` produced by the decision node, or an
            error dict on failure.
        """
        state: AgriState = {
            "input_type": "",
            "text_query": input_data.get("text_query", ""),
            "image_data": input_data.get("image_data"),
            "audio_data": input_data.get("audio_data"),
            "language": input_data.get("language", "ar"),
            "session_id": input_data.get("session_id", ""),
            "vision_result": None,
            "voice_result": None,
            "graph_rag_result": None,
            "vector_result": None,
            "routing_decision": None,
            "fused_result": None,
            "final_response": None,
            "error": None,
        }

        try:
            if self._workflow is not None:
                result = await self._workflow.ainvoke(state)
                return result.get("final_response") or {
                    "error": result.get("error", "No response generated")
                }

            return await self._simple_sequential_process(state)
        except Exception as exc:
            logger.error("Orchestrator process failed: %s", exc, exc_info=True)
            return {"error": str(exc)}

    # ── Sequential fallback ──────────────────────────────────────────────

    async def _simple_sequential_process(self, state: AgriState) -> dict:
        """Execute the pipeline sequentially without LangGraph.

        Mirrors the graph topology but calls each node function in
        sequence, passing state forward.
        """
        logger.info("Running sequential fallback pipeline")

        try:
            # 1. Route
            state = await router_node(state)

            # 2. Modality-specific processing
            input_type = state.get("input_type", "text")
            if input_type == "image":
                state = await vision_node(state)
            elif input_type == "voice":
                state = await voice_node(state)

            # 3. Knowledge retrieval
            state = await edgequake_node(state)
            state = await vector_rag_node(state)

            # 4. Fusion
            state = await fusion_node(state)

            # 5. Decision
            state = await decision_node(state)

            return state.get("final_response") or {
                "error": state.get("error", "No response generated")
            }
        except Exception as exc:
            logger.error("Sequential fallback failed: %s", exc, exc_info=True)
            return {"error": str(exc)}
