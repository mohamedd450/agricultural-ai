"""Decision router that selects the best response strategy."""

from __future__ import annotations

from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionRouter:
    """Route queries to the most appropriate knowledge source.

    The router inspects confidence scores from the vision, graph-RAG, and
    vector-DB pipelines and selects a strategy for fusing the results.
    """

    VISION_THRESHOLD: float = 0.85
    GRAPH_RAG_THRESHOLD: float = 0.7

    def __init__(self) -> None:
        self.vision_threshold = self.VISION_THRESHOLD
        self.graph_rag_threshold = self.GRAPH_RAG_THRESHOLD

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    async def route(
        self,
        vision_result: Optional[dict] = None,
        graph_rag_result: Optional[dict] = None,
        vector_result: Optional[dict] = None,
        has_image: bool = False,
    ) -> dict:
        """Decide on a response strategy based on source confidences.

        Returns
        -------
        dict
            ``{"strategy": str, "primary_source": str,
              "confidence": float, "reasoning": str}``
        """
        vision_conf = self._get_confidence(vision_result)
        graph_conf = self._get_confidence(graph_rag_result)
        vector_conf = self._get_confidence(vector_result)

        if has_image and vision_conf > self.vision_threshold:
            strategy = "vision_primary"
            primary_source = "vision"
            confidence = vision_conf
            reasoning = (
                f"Image provided with high vision confidence ({vision_conf:.2f} "
                f"> {self.vision_threshold})"
            )
        elif graph_conf > self.graph_rag_threshold:
            strategy = "graph_primary"
            primary_source = "graph_rag"
            confidence = graph_conf
            reasoning = (
                f"Graph-RAG confidence is high ({graph_conf:.2f} "
                f"> {self.graph_rag_threshold})"
            )
        else:
            strategy = "fusion"
            primary_source = "combined"
            confidence = max(vision_conf, graph_conf, vector_conf)
            reasoning = (
                "No single source exceeds its threshold – "
                f"fusing all sources (vision={vision_conf:.2f}, "
                f"graph={graph_conf:.2f}, vector={vector_conf:.2f})"
            )

        logger.info(
            "Routing decision: strategy=%s, primary_source=%s, confidence=%.2f",
            strategy,
            primary_source,
            confidence,
        )

        return {
            "strategy": strategy,
            "primary_source": primary_source,
            "confidence": confidence,
            "reasoning": reasoning,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_confidence(self, result: Optional[dict]) -> float:
        """Safely extract a ``confidence`` value from a result dict."""
        if result is None:
            return 0.0
        try:
            return float(result.get("confidence", 0.0))
        except (TypeError, ValueError):
            return 0.0
