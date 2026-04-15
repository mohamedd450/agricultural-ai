"""Vector database service using Qdrant.

Provides semantic search, upsert, and delete operations against a
Qdrant collection dedicated to agricultural embeddings.
"""

import hashlib
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


def _try_load_qdrant():
    """Attempt to import qdrant-client components."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            Distance,
            PointStruct,
            VectorParams,
        )

        return QdrantClient, Distance, PointStruct, VectorParams
    except ImportError:
        logger.warning("qdrant-client not available – vector DB disabled")
        return None, None, None, None


class VectorDBService:
    """Qdrant vector database client for semantic agricultural search.

    Manages a single collection whose name is read from application
    settings.  The collection is created automatically on first use
    if it does not already exist.

    Args:
        client: Optional pre-configured ``QdrantClient`` for testing.
    """

    DEFAULT_VECTOR_SIZE = 384  # sentence-transformers/all-MiniLM-L6-v2

    def __init__(self, client: Any = None) -> None:
        self._settings = get_settings()
        (
            self._QdrantClient,
            self._Distance,
            self._PointStruct,
            self._VectorParams,
        ) = _try_load_qdrant()

        self._client = client
        self._collection: str = self._settings.qdrant_collection_name

        if self._client is None and self._QdrantClient is not None:
            self._client = self._create_client()

        if self._client is not None:
            self._ensure_collection()

        logger.info(
            "VectorDBService initialised (collection=%s, available=%s)",
            self._collection,
            self._client is not None,
        )

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    def _create_client(self) -> Any:
        """Create a ``QdrantClient`` from application settings."""
        if self._QdrantClient is None:
            return None
        try:
            client = self._QdrantClient(
                host=self._settings.qdrant_host,
                port=self._settings.qdrant_port,
            )
            logger.info(
                "Connected to Qdrant at %s:%s",
                self._settings.qdrant_host,
                self._settings.qdrant_port,
            )
            return client
        except Exception:
            logger.exception("Failed to connect to Qdrant")
            return None

    def _ensure_collection(self) -> None:
        """Create the target collection if it does not already exist."""
        if self._client is None or self._VectorParams is None:
            return
        try:
            collections = self._client.get_collections().collections
            names = [c.name for c in collections]
            if self._collection not in names:
                self._client.create_collection(
                    collection_name=self._collection,
                    vectors_config=self._VectorParams(
                        size=self.DEFAULT_VECTOR_SIZE,
                        distance=self._Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection '%s'", self._collection)
            else:
                logger.debug("Collection '%s' already exists", self._collection)
        except Exception:
            logger.exception("Failed to ensure collection '%s'", self._collection)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        limit: int = 5,
        language: str = "en",
    ) -> list[dict]:
        """Search for similar documents by query text.

        The query is converted to a pseudo-vector via a lightweight
        hash-based embedding when a real encoder is unavailable.

        Args:
            query: Free-text search query.
            limit: Maximum number of results.
            language: Language hint passed through in payloads.

        Returns:
            A list of result dicts with ``id``, ``score``, and
            ``payload`` keys.
        """
        logger.info("Vector search: '%s' (limit=%d, lang=%s)", query, limit, language)

        if self._client is None:
            logger.warning("Qdrant unavailable – returning empty results")
            return []

        try:
            query_vector = self._text_to_vector(query)
            results = self._client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                limit=limit,
            )
            return [
                {
                    "id": str(hit.id),
                    "score": round(hit.score, 4),
                    "payload": hit.payload or {},
                }
                for hit in results
            ]
        except Exception:
            logger.exception("Vector search failed")
            return []

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    async def upsert(
        self,
        id: str,
        vector: list[float],
        payload: dict,
    ) -> bool:
        """Insert or update a single point in the collection.

        Args:
            id: Unique point identifier.
            vector: Dense embedding vector.
            payload: Metadata dict stored alongside the vector.

        Returns:
            ``True`` on success, ``False`` otherwise.
        """
        logger.info("Upserting point '%s' (%d dims)", id, len(vector))

        if self._client is None or self._PointStruct is None:
            logger.warning("Qdrant unavailable – upsert skipped")
            return False

        try:
            self._client.upsert(
                collection_name=self._collection,
                points=[
                    self._PointStruct(
                        id=self._stable_int_id(id),
                        vector=vector,
                        payload={**payload, "_str_id": id},
                    )
                ],
            )
            logger.info("Point '%s' upserted successfully", id)
            return True
        except Exception:
            logger.exception("Upsert failed for point '%s'", id)
            return False

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, id: str) -> bool:
        """Delete a point from the collection.

        Args:
            id: The point identifier to remove.

        Returns:
            ``True`` on success, ``False`` otherwise.
        """
        logger.info("Deleting point '%s'", id)

        if self._client is None:
            logger.warning("Qdrant unavailable – delete skipped")
            return False

        try:
            self._client.delete(
                collection_name=self._collection,
                points_selector=[self._stable_int_id(id)],
            )
            logger.info("Point '%s' deleted", id)
            return True
        except Exception:
            logger.exception("Delete failed for point '%s'", id)
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _text_to_vector(self, text: str) -> list[float]:
        """Convert text to a deterministic pseudo-vector.

        This is a lightweight stand-in for a real sentence encoder.
        In production, swap this for a proper embedding model call.
        """
        digest = hashlib.sha256(text.encode()).digest()
        raw = [b / 255.0 for b in digest]
        # Repeat / truncate to match the configured vector size
        vector = (raw * (self.DEFAULT_VECTOR_SIZE // len(raw) + 1))[
            : self.DEFAULT_VECTOR_SIZE
        ]
        return vector

    @staticmethod
    def _stable_int_id(string_id: str) -> int:
        """Derive a stable positive integer from a string ID.

        Qdrant accepts either string or integer point IDs; using
        integers avoids UUID-format requirements.
        """
        return int(hashlib.md5(string_id.encode()).hexdigest()[:15], 16)
