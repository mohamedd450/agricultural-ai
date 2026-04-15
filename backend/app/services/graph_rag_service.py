"""Graph-RAG service for EdgeQuake knowledge-graph integration."""

from __future__ import annotations

from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:  # pragma: no cover
    AIOHTTP_AVAILABLE = False
    logger.warning(
        "aiohttp not installed – GraphRAGService will be unavailable"
    )


class GraphRAGService:
    """Query an EdgeQuake graph-RAG backend for multi-hop reasoning."""

    def __init__(self, endpoint: str = "http://localhost:8081") -> None:
        self.endpoint = endpoint
        self.session: Optional[object] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Create the underlying HTTP client session."""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp unavailable – cannot initialise session")
            return

        try:
            self.session = aiohttp.ClientSession()
            logger.info(
                "GraphRAGService initialised with endpoint %s", self.endpoint
            )
        except Exception:
            logger.error(
                "Failed to create aiohttp session", exc_info=True
            )
            self.session = None

    async def close(self) -> None:
        """Close the HTTP client session."""
        if self.session is not None:
            try:
                await self.session.close()  # type: ignore[union-attr]
                logger.info("GraphRAGService session closed")
            except Exception:
                logger.error(
                    "Error closing GraphRAGService session", exc_info=True
                )
            finally:
                self.session = None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def query(
        self,
        question: str,
        context: Optional[dict] = None,
        language: str = "ar",
    ) -> dict:
        """Send a question to the EdgeQuake ``/query`` endpoint.

        Returns
        -------
        dict
            ``{"answer": str, "confidence": float,
              "graph_paths": list[str], "reasoning_steps": list[str]}``
        """
        if self.session is None:
            logger.warning("GraphRAGService session not available")
            return self._fallback_response()

        payload: dict = {"question": question, "context": context}
        try:
            async with self.session.post(  # type: ignore[union-attr]
                f"{self.endpoint}/query",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                data: dict = await resp.json()
                return {
                    "answer": data.get("answer", ""),
                    "confidence": float(data.get("confidence", 0.0)),
                    "graph_paths": data.get("graph_paths", []),
                    "reasoning_steps": data.get("reasoning_steps", []),
                }
        except Exception:
            logger.error(
                "EdgeQuake /query request failed for question: %s",
                question,
                exc_info=True,
            )
            return self._fallback_response()

    async def multi_hop_reasoning(
        self,
        question: str,
        max_hops: int = 3,
    ) -> dict:
        """Perform multi-hop reasoning via the ``/multi-hop`` endpoint.

        Returns
        -------
        dict
            Result dict with ``paths`` and other reasoning metadata.
        """
        if self.session is None:
            logger.warning("GraphRAGService session not available")
            return self._fallback_response()

        payload: dict = {"question": question, "max_hops": max_hops}
        try:
            async with self.session.post(  # type: ignore[union-attr]
                f"{self.endpoint}/multi-hop",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                data: dict = await resp.json()
                return {
                    "answer": data.get("answer", ""),
                    "confidence": float(data.get("confidence", 0.0)),
                    "graph_paths": data.get("graph_paths", []),
                    "reasoning_steps": data.get("reasoning_steps", []),
                    "paths": data.get("paths", []),
                }
        except Exception:
            logger.error(
                "EdgeQuake /multi-hop request failed for question: %s",
                question,
                exc_info=True,
            )
            return self._fallback_response()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_response() -> dict:
        """Return a safe fallback when the EdgeQuake backend is unreachable."""
        return {
            "answer": "",
            "confidence": 0.0,
            "graph_paths": [],
            "reasoning_steps": [],
        }

    @property
    def is_available(self) -> bool:
        """Return ``True`` when the HTTP session is ready."""
        return self.session is not None
