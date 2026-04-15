from __future__ import annotations

import logging
import uuid

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except ImportError:
    QdrantClient = None  # type: ignore[assignment, misc]
    Distance = None  # type: ignore[assignment, misc]
    PointStruct = None  # type: ignore[assignment, misc]
    VectorParams = None  # type: ignore[assignment, misc]

# Default embedding dimension for all-MiniLM-L6-v2
_DEFAULT_VECTOR_SIZE = 384


class QdrantLoader:
    """Load document embeddings into a Qdrant vector store."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "agricultural_knowledge",
    ) -> None:
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._client = None

    async def initialize(self) -> None:
        """Create the Qdrant client and ensure the collection exists."""
        if QdrantClient is None:
            raise RuntimeError(
                "qdrant-client is not installed. "
                "Run: pip install qdrant-client"
            )

        self._client = QdrantClient(host=self.host, port=self.port)

        collections = [
            c.name for c in self._client.get_collections().collections
        ]
        if self.collection_name not in collections:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=_DEFAULT_VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", self.collection_name)
        else:
            logger.info(
                "Qdrant collection already exists: %s", self.collection_name
            )

    async def load_documents(
        self,
        documents: list[dict],
        embeddings: list[list[float]],
    ) -> int:
        """Upsert documents with their embeddings into Qdrant.

        Returns the number of documents loaded.
        """
        if self._client is None:
            raise RuntimeError("Client not initialised. Call initialize() first.")

        if len(documents) != len(embeddings):
            raise ValueError(
                f"Document count ({len(documents)}) does not match "
                f"embedding count ({len(embeddings)})."
            )

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "chunk_index": doc.get("chunk_index"),
                },
            )
            for doc, embedding in zip(documents, embeddings)
        ]

        self._client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info(
            "Loaded %d documents into Qdrant collection '%s'",
            len(points),
            self.collection_name,
        )
        return len(points)

    async def close(self) -> None:
        """Close the Qdrant client connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("Qdrant client connection closed.")
