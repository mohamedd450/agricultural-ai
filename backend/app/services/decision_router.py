"""Confidence-based decision routing for multi-source diagnostics.

Determines which analysis source(s) to trust and how to weight
their contributions to the final diagnosis.
"""

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

# Routing thresholds – tuned on agricultural image/graph diagnostic benchmarks.
# VISION_HIGH_CONFIDENCE: above this the CNN prediction alone is reliable.
# GRAPH_HIGH_CONFIDENCE: above this the knowledge-graph reasoning is reliable.
# LOW_CONFIDENCE: below this for *all* sources we fall back to vector search.
VISION_HIGH_CONFIDENCE = 0.85
GRAPH_HIGH_CONFIDENCE = 0.70
LOW_CONFIDENCE = 0.30

# Source weights for weighted combination
DEFAULT_WEIGHTS = {
    "vision": 0.45,
    "graph_rag": 0.35,
    "vector": 0.20,
}


class DecisionRouter:
    """Routes diagnostic decisions across vision, Graph-RAG, and vector sources.

    Uses configurable confidence thresholds to decide which source(s)
    to trust, then produces a combined result with an explanation.

    Args:
        weights: Optional custom weight dict overriding ``DEFAULT_WEIGHTS``.
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._settings = get_settings()
        self._weights = weights or DEFAULT_WEIGHTS.copy()
        logger.info("DecisionRouter initialised (weights=%s)", self._weights)

    # ------------------------------------------------------------------
    # Main routing
    # ------------------------------------------------------------------

    def route(
        self,
        vision_result: dict,
        graph_rag_result: dict,
        vector_result: dict,
    ) -> dict:
        """Select the best diagnosis strategy based on source confidences.

        Args:
            vision_result: Output from ``VisionService.analyze_image``.
                Expected keys: ``class``, ``confidence``, ``label``.
            graph_rag_result: Serialised ``GraphRAGResponse``.
                Expected keys: ``answer``, ``confidence``,
                ``graph_paths``, ``reasoning_steps``.
            vector_result: Payload list from ``VectorDBService.search``.
                Should contain dicts with ``score`` and ``payload``.

        Returns:
            A dict with ``diagnosis``, ``confidence``, ``strategy``,
            ``sources_used``, ``explanation``, and ``details``.
        """
        v_conf = float(vision_result.get("confidence", 0))
        g_conf = float(graph_rag_result.get("confidence", 0))
        vec_conf = self._vector_confidence(vector_result)

        logger.info(
            "Routing – vision=%.2f, graph=%.2f, vector=%.2f",
            v_conf,
            g_conf,
            vec_conf,
        )

        # Strategy selection
        if v_conf > VISION_HIGH_CONFIDENCE and g_conf > GRAPH_HIGH_CONFIDENCE:
            return self._both_high(vision_result, graph_rag_result, v_conf, g_conf)

        if v_conf > VISION_HIGH_CONFIDENCE:
            return self._vision_primary(vision_result, v_conf)

        if g_conf > GRAPH_HIGH_CONFIDENCE:
            return self._graph_primary(graph_rag_result, g_conf)

        if v_conf > LOW_CONFIDENCE or g_conf > LOW_CONFIDENCE:
            return self._weighted_combination(
                vision_result, graph_rag_result, vector_result,
                v_conf, g_conf, vec_conf,
            )

        # Last resort: vector RAG fallback
        return self._vector_fallback(vector_result, vec_conf)

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _vision_primary(self, vision: dict, v_conf: float) -> dict:
        return {
            "diagnosis": vision.get("label") or vision.get("class", "unknown"),
            "confidence": v_conf,
            "strategy": "vision_primary",
            "sources_used": ["vision"],
            "explanation": (
                f"High-confidence vision result ({v_conf:.0%}). "
                "Trusting image analysis as primary source."
            ),
            "details": {"vision": vision},
        }

    def _graph_primary(self, graph: dict, g_conf: float) -> dict:
        return {
            "diagnosis": graph.get("answer", ""),
            "confidence": g_conf,
            "strategy": "graph_primary",
            "sources_used": ["graph_rag"],
            "explanation": (
                f"High-confidence graph reasoning ({g_conf:.0%}). "
                "Trusting knowledge graph as primary source."
            ),
            "details": {"graph_rag": graph},
        }

    def _both_high(
        self, vision: dict, graph: dict, v_conf: float, g_conf: float
    ) -> dict:
        combined = self.calculate_combined_confidence(
            [
                {"source": "vision", "confidence": v_conf},
                {"source": "graph_rag", "confidence": g_conf},
            ]
        )
        diagnosis_parts: list[str] = []
        if vision.get("label"):
            diagnosis_parts.append(vision["label"])
        if graph.get("answer"):
            diagnosis_parts.append(graph["answer"])

        return {
            "diagnosis": " | ".join(diagnosis_parts) if diagnosis_parts else "unknown",
            "confidence": combined,
            "strategy": "combined_high",
            "sources_used": ["vision", "graph_rag"],
            "explanation": (
                f"Both vision ({v_conf:.0%}) and graph ({g_conf:.0%}) "
                "report high confidence. Using weighted combination."
            ),
            "details": {"vision": vision, "graph_rag": graph},
        }

    def _weighted_combination(
        self,
        vision: dict,
        graph: dict,
        vector: dict,
        v_conf: float,
        g_conf: float,
        vec_conf: float,
    ) -> dict:
        combined = self.calculate_combined_confidence(
            [
                {"source": "vision", "confidence": v_conf},
                {"source": "graph_rag", "confidence": g_conf},
                {"source": "vector", "confidence": vec_conf},
            ]
        )
        sources_used = []
        if v_conf > LOW_CONFIDENCE:
            sources_used.append("vision")
        if g_conf > LOW_CONFIDENCE:
            sources_used.append("graph_rag")
        if vec_conf > LOW_CONFIDENCE:
            sources_used.append("vector")

        parts: list[str] = []
        if vision.get("label"):
            parts.append(f"Vision: {vision['label']}")
        if graph.get("answer"):
            parts.append(f"Graph: {graph['answer']}")

        return {
            "diagnosis": " | ".join(parts) if parts else "Inconclusive",
            "confidence": combined,
            "strategy": "weighted_combination",
            "sources_used": sources_used or ["vector"],
            "explanation": (
                f"Moderate confidence across sources "
                f"(v={v_conf:.0%}, g={g_conf:.0%}, vec={vec_conf:.0%}). "
                "Using weighted average of all sources."
            ),
            "details": {
                "vision": vision,
                "graph_rag": graph,
                "vector": vector,
            },
        }

    def _vector_fallback(self, vector: dict, vec_conf: float) -> dict:
        best_match = ""
        if isinstance(vector, list) and vector:
            best_match = (
                vector[0].get("payload", {}).get("diagnosis", "")
                or vector[0].get("payload", {}).get("text", "")
            )

        return {
            "diagnosis": best_match or "Unable to determine diagnosis",
            "confidence": vec_conf,
            "strategy": "vector_fallback",
            "sources_used": ["vector"],
            "explanation": (
                "Low confidence from vision and graph sources. "
                "Falling back to vector similarity search."
            ),
            "details": {"vector": vector},
        }

    # ------------------------------------------------------------------
    # Confidence calculation
    # ------------------------------------------------------------------

    def calculate_combined_confidence(self, sources: list[dict]) -> float:
        """Compute a weighted confidence score from multiple sources.

        Args:
            sources: List of dicts each with ``source`` (name) and
                ``confidence`` (float 0–1).

        Returns:
            A single combined confidence in [0, 1].
        """
        if not sources:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for s in sources:
            name = s.get("source", "")
            conf = float(s.get("confidence", 0))
            w = self._weights.get(name, 0.1)
            weighted_sum += conf * w
            total_weight += w

        if total_weight == 0:
            return 0.0

        combined = round(weighted_sum / total_weight, 4)
        logger.debug("Combined confidence: %.4f (from %d sources)", combined, len(sources))
        return combined

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    @staticmethod
    def get_routing_explanation(decision: dict) -> str:
        """Return a human-readable summary of a routing decision.

        Args:
            decision: The dict returned by :meth:`route`.

        Returns:
            Multi-line explanation string.
        """
        lines = [
            f"Strategy: {decision.get('strategy', 'unknown')}",
            f"Confidence: {decision.get('confidence', 0):.0%}",
            f"Sources: {', '.join(decision.get('sources_used', []))}",
        ]
        explanation = decision.get("explanation", "")
        if explanation:
            lines.append(f"Reasoning: {explanation}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _vector_confidence(vector_result: dict | list) -> float:
        """Extract an aggregate confidence from vector search results."""
        if isinstance(vector_result, list) and vector_result:
            scores = [float(r.get("score", 0)) for r in vector_result]
            return round(sum(scores) / len(scores), 4)
        return 0.0
