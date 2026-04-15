"""Fusion service that merges results from multiple knowledge sources."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class FusionService:
    """Combine vision, graph-RAG, and vector-DB outputs into a single response."""

    VISION_WEIGHT: float = 0.3
    GRAPH_RAG_WEIGHT: float = 0.4
    VECTOR_DB_WEIGHT: float = 0.3

    # ------------------------------------------------------------------
    # Fusion
    # ------------------------------------------------------------------

    async def fuse(
        self,
        vision_result: Optional[dict] = None,
        graph_rag_result: Optional[dict] = None,
        vector_result: Optional[dict] = None,
        routing_decision: Optional[dict] = None,
        language: str = "ar",
    ) -> dict:
        """Fuse multiple source results into a unified diagnosis response.

        Returns a dict compatible with
        :class:`~app.models.response_models.DiagnosisResponse`.
        """
        vision_conf = self._safe_confidence(vision_result)
        graph_conf = self._safe_confidence(graph_rag_result)
        vector_conf = self._safe_confidence(vector_result)

        fused_score = (
            vision_conf * self.VISION_WEIGHT
            + graph_conf * self.GRAPH_RAG_WEIGHT
            + vector_conf * self.VECTOR_DB_WEIGHT
        )

        strategy = (
            routing_decision.get("strategy", "fusion")
            if routing_decision
            else "fusion"
        )

        sources = {
            "vision": vision_result,
            "graph_rag": graph_rag_result,
            "vector": vector_result,
        }

        diagnosis, treatment = self._select_best_diagnosis(sources, strategy)
        graph_paths = self._merge_graph_paths(
            vision_result, graph_rag_result, vector_result
        )
        explanation = self._generate_explanation(strategy, sources, language)

        primary_source = (
            routing_decision.get("primary_source", "combined")
            if routing_decision
            else "combined"
        )

        logger.info(
            "Fused result: strategy=%s, confidence=%.2f, source=%s",
            strategy,
            fused_score,
            primary_source,
        )

        return {
            "diagnosis": diagnosis,
            "treatment": treatment,
            "confidence": round(fused_score, 4),
            "graph_paths": graph_paths,
            "explanation": explanation,
            "source": primary_source,
            "language": language,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _merge_graph_paths(self, *results: Optional[dict]) -> list[str]:
        """Collect all ``graph_paths`` entries from the provided results."""
        paths: list[str] = []
        for result in results:
            if result is None:
                continue
            result_paths = result.get("graph_paths", [])
            if isinstance(result_paths, list):
                for path in result_paths:
                    if isinstance(path, str) and path not in paths:
                        paths.append(path)
        return paths

    def _generate_explanation(
        self,
        strategy: str,
        sources: dict,
        language: str,
    ) -> str:
        """Build a human-readable explanation of the fusion process."""
        active_sources = [
            name
            for name, result in sources.items()
            if result is not None and self._safe_confidence(result) > 0.0
        ]

        if language == "ar":
            if strategy == "vision_primary":
                return (
                    "تم التشخيص بشكل أساسي من تحليل الصورة"
                    f" باستخدام {len(active_sources)} مصادر"
                )
            if strategy == "graph_primary":
                return (
                    "تم التشخيص بشكل أساسي من قاعدة المعرفة"
                    f" باستخدام {len(active_sources)} مصادر"
                )
            return (
                "تم التشخيص من دمج"
                f" {len(active_sources)} مصادر معرفية"
            )

        # Default: English
        if strategy == "vision_primary":
            return (
                f"Diagnosis primarily from image analysis "
                f"using {len(active_sources)} source(s)"
            )
        if strategy == "graph_primary":
            return (
                f"Diagnosis primarily from knowledge graph "
                f"using {len(active_sources)} source(s)"
            )
        return (
            f"Diagnosis from fusion of "
            f"{len(active_sources)} knowledge source(s)"
        )

    def _select_best_diagnosis(
        self,
        results: dict,
        strategy: str,
    ) -> tuple[str, str]:
        """Pick the best diagnosis and treatment based on the routing strategy.

        Returns
        -------
        tuple[str, str]
            ``(diagnosis, treatment)``
        """
        # Strategy-ordered source preference
        if strategy == "vision_primary":
            order = ["vision", "graph_rag", "vector"]
        elif strategy == "graph_primary":
            order = ["graph_rag", "vision", "vector"]
        else:
            order = ["graph_rag", "vector", "vision"]

        for source_name in order:
            result = results.get(source_name)
            if result is None:
                continue

            diagnosis = result.get("diagnosis") or result.get("answer") or ""
            treatment = result.get("treatment", "")

            if diagnosis:
                return diagnosis, treatment

        return "", ""

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_confidence(result: Optional[dict]) -> float:
        """Extract a numeric confidence from *result*, defaulting to ``0.0``."""
        if result is None:
            return 0.0
        try:
            return float(result.get("confidence", 0.0))
        except (TypeError, ValueError):
            return 0.0
