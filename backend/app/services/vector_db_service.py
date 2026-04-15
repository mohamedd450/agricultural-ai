"""Vector database service backed by Qdrant for semantic search."""

from __future__ import annotations

from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        PointStruct,
        VectorParams,
    )

    QDRANT_AVAILABLE = True
except ImportError:  # pragma: no cover
    QDRANT_AVAILABLE = False
    logger.warning(
        "qdrant-client not installed – VectorDBService will be unavailable"
    )


class VectorDBService:
    """Async-friendly Qdrant wrapper for agricultural knowledge retrieval."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "agricultural_knowledge",
    ) -> None:
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client: Optional[object] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Create a Qdrant client connection."""
        if not QDRANT_AVAILABLE:
            logger.warning(
                "qdrant-client unavailable – cannot initialise VectorDBService"
            )
            return

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(
                "VectorDBService connected to Qdrant at %s:%d",
                self.host,
                self.port,
            )
        except Exception:
            logger.error(
                "Failed to connect to Qdrant at %s:%d",
                self.host,
                self.port,
                exc_info=True,
            )
            self.client = None

    async def close(self) -> None:
        """Close the Qdrant client."""
        if self.client is not None:
            try:
                self.client.close()  # type: ignore[union-attr]
                logger.info("VectorDBService client closed")
            except Exception:
                logger.error(
                    "Error closing VectorDBService client", exc_info=True
                )
            finally:
                self.client = None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query_text: str,
        limit: int = 5,
    ) -> dict:
        """Perform a semantic search over the collection.

        Returns
        -------
        dict
            ``{"results": list[dict], "confidence": float}``
            Each result: ``{"text": str, "score": float, "metadata": dict}``
        """
        if self.client is None:
            return {"results": [], "confidence": 0.0}

        try:
            query_vector = self._encode_text(query_text)
            hits = self.client.search(  # type: ignore[union-attr]
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
            )

            results: list[dict] = []
            for hit in hits:
                payload = hit.payload or {}
                results.append(
                    {
                        "text": payload.get("text", ""),
                        "score": float(hit.score),
                        "metadata": {
                            k: v for k, v in payload.items() if k != "text"
                        },
                    }
                )

            confidence = results[0]["score"] if results else 0.0
            return {"results": results, "confidence": confidence}
        except Exception:
            logger.error(
                "Vector search failed for query: %s", query_text, exc_info=True
            )
            return {"results": [], "confidence": 0.0}

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------

    async def add_documents(self, documents: list[dict]) -> bool:
        """Upsert documents into the collection.

        Each document dict should contain at least ``"id"``, ``"text"``,
        and optionally ``"metadata"``.
        """
        if self.client is None:
            logger.warning("VectorDBService client not available")
            return False

        if not QDRANT_AVAILABLE:
            return False

        try:
            points: list[PointStruct] = []
            for doc in documents:
                vector = self._encode_text(doc.get("text", ""))
                payload = {"text": doc.get("text", "")}
                payload.update(doc.get("metadata", {}))
                points.append(
                    PointStruct(
                        id=doc["id"],
                        vector=vector,
                        payload=payload,
                    )
                )

            self.client.upsert(  # type: ignore[union-attr]
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(
                "Upserted %d documents into collection '%s'",
                len(points),
                self.collection_name,
            )
            return True
        except Exception:
            logger.error(
                "Failed to upsert documents into collection '%s'",
                self.collection_name,
                exc_info=True,
            )
            return False

    async def ensure_collection(self) -> None:
        """Create the vector collection if it does not already exist."""
        if self.client is None or not QDRANT_AVAILABLE:
            logger.warning("Cannot ensure collection – client unavailable")
            return

        try:
            collections = self.client.get_collections().collections  # type: ignore[union-attr]
            existing_names = [c.name for c in collections]

            if self.collection_name not in existing_names:
                self.client.create_collection(  # type: ignore[union-attr]
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(
                    "Created Qdrant collection '%s' (size=384, cosine)",
                    self.collection_name,
                )
            else:
                logger.info(
                    "Collection '%s' already exists", self.collection_name
                )
        except Exception:
            logger.error(
                "Failed to ensure collection '%s'",
                self.collection_name,
                exc_info=True,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_text(text: str) -> list[float]:
        """Produce a simple deterministic 384-d vector from *text*.

        In production this should be replaced with a proper embedding model
        (e.g. ``sentence-transformers/all-MiniLM-L6-v2``).
        """
        import hashlib

        digest = hashlib.sha384(text.encode("utf-8")).digest()
        raw = [float(b) / 255.0 for b in digest]
        # Pad / truncate to exactly 384 dimensions
        vector = (raw * (384 // len(raw) + 1))[:384]
        return vector

    @property
    def is_available(self) -> bool:
        """Return ``True`` when the Qdrant client is ready."""
        return self.client is not None
