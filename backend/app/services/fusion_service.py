"""Fusion service for combining multi-source diagnostic outputs.

Merges vision, Graph-RAG, and vector search results into a unified
diagnosis with confidence-weighted reasoning and language-aware
formatting.
"""

import logging
import uuid
from typing import Any

from app.config import get_settings
from app.services.decision_router import DecisionRouter

logger = logging.getLogger(__name__)


class FusionService:
    """Merges outputs from vision, Graph-RAG, and vector search.

    Produces a single unified diagnostic response that includes
    the fused diagnosis, treatment advice, confidence scores,
    graph paths, and a human-readable explanation.

    Args:
        router: Optional ``DecisionRouter`` instance for testing.
    """

    def __init__(self, router: DecisionRouter | None = None) -> None:
        self._settings = get_settings()
        self._router = router or DecisionRouter()
        logger.info("FusionService initialised")

    # ------------------------------------------------------------------
    # Main fusion
    # ------------------------------------------------------------------

    async def fuse(
        self,
        vision_output: dict,
        graph_rag_output: dict,
        vector_output: dict,
        user_context: dict | None = None,
    ) -> dict:
        """Fuse all diagnostic sources into a single response.

        Args:
            vision_output: Result from ``VisionService.analyze_image``.
            graph_rag_output: Serialised ``GraphRAGResponse``.
            vector_output: Result list from ``VectorDBService.search``.
            user_context: Optional user/session context (language, location, etc.).

        Returns:
            A unified diagnostic dict suitable for ``DiagnosisResponse``.
        """
        user_context = user_context or {}
        language = user_context.get("language", "en")
        request_id = user_context.get("request_id", str(uuid.uuid4()))

        logger.info("Fusing outputs (request=%s, lang=%s)", request_id, language)

        # Step 1: route to decide trust strategy
        routing = self._router.route(vision_output, graph_rag_output, vector_output)

        # Step 2: extract components
        diagnosis = self._build_diagnosis(
            routing, vision_output, graph_rag_output, language
        )
        treatment = self._build_treatment(graph_rag_output, vector_output)
        graph_paths = self._extract_graph_paths(graph_rag_output)
        explanation = self._build_explanation(
            routing, vision_output, graph_rag_output, vector_output, language
        )
        sources = self._collect_sources(routing)

        fused = {
            "diagnosis": diagnosis,
            "treatment": treatment,
            "confidence": routing.get("confidence", 0.0),
            "graph_paths": graph_paths,
            "explanation": explanation,
            "language": language,
            "request_id": request_id,
            "sources": sources,
            "routing_strategy": routing.get("strategy", "unknown"),
        }

        logger.info(
            "Fusion complete – strategy=%s, confidence=%.2f",
            fused["routing_strategy"],
            fused["confidence"],
        )
        return fused

    # ------------------------------------------------------------------
    # Diagnosis building
    # ------------------------------------------------------------------

    def _build_diagnosis(
        self,
        routing: dict,
        vision: dict,
        graph: dict,
        language: str,
    ) -> str:
        """Construct the primary diagnosis string."""
        strategy = routing.get("strategy", "")

        if strategy == "vision_primary":
            base = vision.get("label") or vision.get("class", "Unknown")
        elif strategy == "graph_primary":
            base = graph.get("answer", "Unknown")
        elif strategy in ("combined_high", "weighted_combination"):
            vision_label = vision.get("label") or vision.get("class", "")
            graph_answer = graph.get("answer", "")
            parts = [p for p in (vision_label, graph_answer) if p]
            base = ". ".join(parts) if parts else "Inconclusive"
        else:
            base = routing.get("diagnosis", "Unable to determine diagnosis")

        if language == "ar":
            base = self._add_arabic_context(base)

        return base

    @staticmethod
    def _add_arabic_context(text: str) -> str:
        """Wrap diagnosis text with Arabic directional markers."""
        return f"\u200f{text}\u200f"

    # ------------------------------------------------------------------
    # Treatment extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_treatment(graph: dict, vector: list | dict) -> str:
        """Extract the best treatment recommendation."""
        # Prefer graph-sourced treatment
        answer: str = graph.get("answer", "")
        if "treatment" in answer.lower() or "apply" in answer.lower():
            return answer

        reasoning: list[str] = graph.get("reasoning_steps", [])
        for step in reasoning:
            if "treatment" in step.lower() or "apply" in step.lower():
                return step

        # Fall back to vector payloads
        if isinstance(vector, list):
            for item in vector:
                payload = item.get("payload", {})
                treatment = payload.get("treatment") or payload.get("recommendation")
                if treatment:
                    return str(treatment)

        return "Consult a local agricultural extension officer for treatment advice."

    # ------------------------------------------------------------------
    # Graph paths
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_graph_paths(graph: dict) -> list[str]:
        """Extract human-readable graph path summaries."""
        paths: list[str] = graph.get("graph_paths", [])
        if paths:
            return paths

        reasoning: list[str] = graph.get("reasoning_steps", [])
        if reasoning:
            return [f"Step {i + 1}: {s}" for i, s in enumerate(reasoning)]

        return []

    # ------------------------------------------------------------------
    # Explanation generation
    # ------------------------------------------------------------------

    def _build_explanation(
        self,
        routing: dict,
        vision: dict,
        graph: dict,
        vector: list | dict,
        language: str,
    ) -> str:
        """Build a multi-paragraph explanation from all reasoning sources."""
        sections: list[str] = []

        # Routing rationale
        routing_expl = routing.get("explanation", "")
        if routing_expl:
            sections.append(routing_expl)

        # Vision reasoning
        v_conf = vision.get("confidence", 0)
        v_class = vision.get("label") or vision.get("class")
        if v_class and v_conf > 0:
            sections.append(
                f"Image analysis identified '{v_class}' "
                f"with {v_conf:.0%} confidence."
            )
            preds = vision.get("all_predictions", [])
            if len(preds) > 1:
                alt = ", ".join(
                    f"{p['class']} ({p['confidence']:.0%})" for p in preds[1:3]
                )
                sections.append(f"Alternative predictions: {alt}.")

        # Graph reasoning
        g_paths = graph.get("graph_paths", [])
        if g_paths:
            sections.append(
                "Knowledge graph paths: " + " → ".join(g_paths[:3]) + "."
            )

        g_steps = graph.get("reasoning_steps", [])
        if g_steps:
            sections.append(
                "Reasoning: " + "; ".join(g_steps[:3]) + "."
            )

        # Vector context
        if isinstance(vector, list) and vector:
            top_score = vector[0].get("score", 0)
            sections.append(
                f"Similar cases found in knowledge base "
                f"(top similarity: {top_score:.2f})."
            )

        explanation = " ".join(sections)

        if language == "ar":
            explanation = self._add_arabic_context(explanation)

        return explanation

    # ------------------------------------------------------------------
    # Source collection
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_sources(routing: dict) -> list[str]:
        """List the source systems that contributed to the diagnosis."""
        sources = routing.get("sources_used", [])
        label_map = {
            "vision": "Image Analysis Model",
            "graph_rag": "Knowledge Graph (EdgeQuake)",
            "vector": "Vector Similarity Search",
        }
        return [label_map.get(s, s) for s in sources]
