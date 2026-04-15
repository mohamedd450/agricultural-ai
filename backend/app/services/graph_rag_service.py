"""Graph-RAG service wrapping the EdgeQuake knowledge graph engine.

Provides multi-hop graph reasoning for agricultural diagnostics.
Falls back to simple rule-based reasoning when EdgeQuake is
unavailable.
"""

import logging
from typing import Any

import httpx

from app.config import get_settings
from app.models.graph_models import (
    GraphEdge,
    GraphNode,
    GraphPath,
    GraphRAGResponse,
    KnowledgeSubgraph,
)

logger = logging.getLogger(__name__)

# Lightweight knowledge base used when EdgeQuake is unreachable
_FALLBACK_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "nitrogen_deficiency": {
        "treatment": "Apply nitrogen-rich fertilizer (e.g. urea, ammonium nitrate)",
        "related": ["yellowing_leaves", "stunted_growth", "urea"],
        "severity": "moderate",
    },
    "leaf_blight": {
        "treatment": "Apply copper-based fungicide and remove infected leaves",
        "related": ["brown_spots", "wilting", "copper_fungicide"],
        "severity": "high",
    },
    "powdery_mildew": {
        "treatment": "Apply sulfur-based fungicide and improve air circulation",
        "related": ["white_powder", "leaf_curl", "sulfur_fungicide"],
        "severity": "moderate",
    },
    "rust": {
        "treatment": "Apply systemic fungicide and remove infected plant material",
        "related": ["orange_pustules", "leaf_drop", "systemic_fungicide"],
        "severity": "high",
    },
    "bacterial_spot": {
        "treatment": "Apply copper bactericide and practice crop rotation",
        "related": ["water_soaked_lesions", "fruit_spots", "crop_rotation"],
        "severity": "high",
    },
    "healthy": {
        "treatment": "No treatment needed – continue regular care",
        "related": ["good_irrigation", "balanced_nutrition"],
        "severity": "none",
    },
}


class GraphRAGService:
    """EdgeQuake Graph-RAG wrapper for agricultural knowledge queries.

    Sends queries to the EdgeQuake HTTP API and parses the response
    into structured ``GraphRAGResponse`` objects.  When EdgeQuake is
    unreachable, the service falls back to a simple local knowledge
    base.

    Args:
        http_client: Optional ``httpx.AsyncClient`` for testing.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._settings = get_settings()
        self._base_url: str = (
            f"http://{self._settings.edgequake_host}:"
            f"{self._settings.edgequake_port}"
        )
        self._client = http_client
        logger.info("GraphRAGService initialised (endpoint=%s)", self._base_url)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=30.0)

    async def _post(self, path: str, payload: dict) -> dict | None:
        """POST to EdgeQuake and return the JSON body, or *None* on failure."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self._base_url}{path}", json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "EdgeQuake HTTP %s: %s", exc.response.status_code, exc.response.text
            )
            return None
        except httpx.RequestError:
            logger.warning("EdgeQuake unreachable at %s", self._base_url)
            return None
        finally:
            if self._client is None:
                await client.aclose()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def query(
        self,
        question: str,
        context: dict | None = None,
        language: str = "en",
    ) -> GraphRAGResponse:
        """Query the knowledge graph for a single-hop answer.

        Args:
            question: Natural-language question.
            context: Optional context dict (e.g. vision results).
            language: Response language code.

        Returns:
            A ``GraphRAGResponse`` with the answer, graph paths,
            confidence, and reasoning steps.
        """
        logger.info("Graph-RAG query: '%s' (lang=%s)", question, language)

        payload = {
            "question": question,
            "context": context or {},
            "language": language,
        }
        data = await self._post("/api/query", payload)

        if data is not None:
            return self._parse_response(data, language)

        logger.info("Using fallback knowledge base")
        return self._fallback_query(question, context, language)

    async def multi_hop_query(
        self, question: str, max_hops: int = 3
    ) -> GraphRAGResponse:
        """Perform a multi-hop reasoning query across the knowledge graph.

        Args:
            question: Natural-language question.
            max_hops: Maximum traversal depth (1–5).

        Returns:
            A ``GraphRAGResponse`` with multi-step reasoning paths.
        """
        max_hops = max(1, min(max_hops, 5))
        logger.info(
            "Multi-hop query (hops=%d): '%s'", max_hops, question
        )

        payload = {"question": question, "max_hops": max_hops}
        data = await self._post("/api/multi-hop", payload)

        if data is not None:
            return self._parse_response(data)

        return self._fallback_query(question)

    async def get_related_entities(
        self,
        entity: str,
        relationship_type: str | None = None,
    ) -> list[dict]:
        """Retrieve entities related to the given entity.

        Args:
            entity: The source entity identifier.
            relationship_type: Optional filter (e.g. ``"treated_by"``).

        Returns:
            A list of dicts with ``entity``, ``relationship``, and
            ``confidence`` keys.
        """
        logger.info(
            "Related entities: entity='%s', rel=%s",
            entity,
            relationship_type,
        )

        payload: dict[str, Any] = {"entity": entity}
        if relationship_type:
            payload["relationship_type"] = relationship_type

        data = await self._post("/api/related", payload)

        if data is not None and isinstance(data.get("entities"), list):
            return [
                {
                    "entity": e.get("name", ""),
                    "relationship": e.get("relationship", "related_to"),
                    "confidence": e.get("confidence", 0.5),
                }
                for e in data["entities"]
            ]

        # Fallback
        entry = _FALLBACK_KNOWLEDGE.get(entity.lower(), {})
        return [
            {"entity": r, "relationship": "related_to", "confidence": 0.5}
            for r in entry.get("related", [])
        ]

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(
        self, data: dict, language: str = "en"
    ) -> GraphRAGResponse:
        """Parse a raw EdgeQuake JSON response into a ``GraphRAGResponse``."""
        try:
            nodes = [
                GraphNode(
                    id=n.get("id", ""),
                    label=n.get("label", ""),
                    type=n.get("type", "Disease"),
                    properties=n.get("properties", {}),
                    confidence=n.get("confidence"),
                )
                for n in data.get("nodes", [])
            ]
            edges = [
                GraphEdge(
                    source=e.get("source", ""),
                    target=e.get("target", ""),
                    relationship=e.get("relationship", "affects"),
                    weight=e.get("weight", 0.5),
                    properties=e.get("properties", {}),
                )
                for e in data.get("edges", [])
            ]
            paths = [
                GraphPath(
                    nodes=[],
                    edges=[],
                    confidence=p.get("confidence", 0.5),
                    description=p.get("description", ""),
                )
                for p in data.get("paths", [])
            ]
            subgraph = KnowledgeSubgraph(
                nodes=nodes, edges=edges, paths=paths
            )

            return GraphRAGResponse(
                answer=data.get("answer", ""),
                graph_paths=data.get(
                    "graph_paths", [p.description for p in paths]
                ),
                subgraph=subgraph,
                confidence=float(data.get("confidence", 0.5)),
                reasoning_steps=data.get("reasoning_steps", []),
            )
        except Exception:
            logger.exception("Failed to parse EdgeQuake response")
            return self._empty_response()

    # ------------------------------------------------------------------
    # Fallback logic
    # ------------------------------------------------------------------

    def _fallback_query(
        self,
        question: str,
        context: dict | None = None,
        language: str = "en",
    ) -> GraphRAGResponse:
        """Simple rule-based fallback when EdgeQuake is unreachable."""
        question_lower = question.lower()
        context = context or {}

        matched_disease: str | None = None
        for disease in _FALLBACK_KNOWLEDGE:
            normalised = disease.replace("_", " ")
            if normalised in question_lower or disease in question_lower:
                matched_disease = disease
                break

        if matched_disease is None:
            matched_disease = context.get("class")

        if matched_disease and matched_disease in _FALLBACK_KNOWLEDGE:
            info = _FALLBACK_KNOWLEDGE[matched_disease]
            answer = (
                f"Detected: {matched_disease.replace('_', ' ').title()}. "
                f"Recommended treatment: {info['treatment']}. "
                f"Severity: {info['severity']}."
            )
            return GraphRAGResponse(
                answer=answer,
                graph_paths=[
                    f"{matched_disease} -> treatment -> {info['treatment']}",
                    f"{matched_disease} -> severity -> {info['severity']}",
                ],
                subgraph=None,
                confidence=0.6,
                reasoning_steps=[
                    f"Identified disease: {matched_disease}",
                    "Looked up local knowledge base",
                    f"Found treatment: {info['treatment']}",
                ],
            )

        return self._empty_response()

    @staticmethod
    def _empty_response() -> GraphRAGResponse:
        return GraphRAGResponse(
            answer="Unable to determine diagnosis from knowledge graph.",
            graph_paths=[],
            subgraph=None,
            confidence=0.0,
            reasoning_steps=["No matching information found"],
        )
