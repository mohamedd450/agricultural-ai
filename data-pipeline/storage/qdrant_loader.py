"""Qdrant vector database loader for agricultural embeddings."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QdrantLoader:
    """Loads vector embeddings into Qdrant for similarity search."""

    def __init__(self, url: str = "http://localhost:6333") -> None:
        """Initialize the Qdrant loader.

        Args:
            url: Qdrant server URL.
        """
        self._url = url
        self._client: Optional[object] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Qdrant."""
        try:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(url=self._url, timeout=30)
            logger.info("Connected to Qdrant at %s", self._url)
        except Exception as e:
            logger.error("Failed to connect to Qdrant at %s: %s", self._url, e)
            self._client = None

    def create_collection(self, name: str, vector_size: int = 384) -> bool:
        """Create a vector collection in Qdrant.

        Args:
            name: Collection name.
            vector_size: Dimension of vectors.

        Returns:
            True if collection was created successfully.
        """
        if self._client is None:
            logger.error("Qdrant client not connected")
            return False

        try:
            from qdrant_client.models import Distance, VectorParams
            self._client.recreate_collection(  # type: ignore[union-attr]
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Created collection '%s' with vector size %d", name, vector_size)
            return True
        except Exception as e:
            logger.error("Failed to create collection '%s': %s", name, e)
            return False

    def load_vectors(
        self, collection: str, vectors: list, payloads: list
    ) -> int:
        """Load vectors with payloads into a collection.

        Args:
            collection: Target collection name.
            vectors: List of vector embeddings.
            payloads: List of payload dicts corresponding to vectors.

        Returns:
            Number of vectors loaded.
        """
        if self._client is None:
            logger.error("Qdrant client not connected")
            return 0

        try:
            from qdrant_client.models import PointStruct
            points = [
                PointStruct(id=i, vector=vec, payload=pay)
                for i, (vec, pay) in enumerate(zip(vectors, payloads))
            ]
            self._client.upsert(collection_name=collection, points=points)  # type: ignore[union-attr]
            logger.info("Loaded %d vectors into '%s'", len(points), collection)
            return len(points)
        except Exception as e:
            logger.error("Failed to load vectors into '%s': %s", collection, e)
            return 0

    def batch_upsert(self, collection: str, data: list[dict]) -> int:
        """Batch upsert documents with vectors and payloads.

        Each item in data should have 'vector' and 'payload' keys.

        Args:
            collection: Target collection name.
            data: List of dicts with 'vector' and 'payload' keys.

        Returns:
            Number of records upserted.
        """
        if self._client is None:
            logger.error("Qdrant client not connected")
            return 0

        try:
            from qdrant_client.models import PointStruct
            batch_size = 100
            total = 0

            for i in range(0, len(data), batch_size):
                batch = data[i: i + batch_size]
                points = [
                    PointStruct(
                        id=i + j,
                        vector=item["vector"],
                        payload=item.get("payload", {}),
                    )
                    for j, item in enumerate(batch)
                ]
                self._client.upsert(collection_name=collection, points=points)  # type: ignore[union-attr]
                total += len(points)

            logger.info("Batch upserted %d records into '%s'", total, collection)
            return total
        except Exception as e:
            logger.error("Batch upsert failed for '%s': %s", collection, e)
            return 0
