"""EdgeQuake indexing client for graph-enhanced search."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EdgeQuakeIndexer:
    """Indexes documents into EdgeQuake for graph-enhanced retrieval."""

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        """Initialize the EdgeQuake indexer.

        Args:
            base_url: EdgeQuake service base URL.
        """
        self._base_url = base_url.rstrip("/")
        self._client: Optional[object] = None
        self._available = False
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the HTTP client and check service availability."""
        try:
            import httpx
            self._client = httpx.Client(base_url=self._base_url, timeout=30.0)
            response = self._client.get("/health")  # type: ignore[union-attr]
            self._available = response.status_code == 200
            if self._available:
                logger.info("EdgeQuake service available at %s", self._base_url)
            else:
                logger.warning("EdgeQuake service returned status %d", response.status_code)
        except Exception as e:
            logger.warning("EdgeQuake service unavailable at %s: %s", self._base_url, e)
            self._available = False

    def index_document(self, doc_id: str, text: str, metadata: dict) -> bool:
        """Index a single document in EdgeQuake.

        Args:
            doc_id: Unique document identifier.
            text: Document text content.
            metadata: Additional metadata for the document.

        Returns:
            True if document was indexed successfully.
        """
        if not self._available or self._client is None:
            logger.warning("EdgeQuake unavailable, skipping document indexing")
            return False

        try:
            payload = {
                "id": doc_id,
                "text": text,
                "metadata": metadata,
            }
            response = self._client.post("/api/v1/documents", json=payload)  # type: ignore[union-attr]
            if response.status_code in (200, 201):
                logger.debug("Indexed document %s", doc_id)
                return True
            logger.warning("Failed to index document %s: HTTP %d", doc_id, response.status_code)
            return False
        except Exception as e:
            logger.error("Error indexing document %s: %s", doc_id, e)
            return False

    def batch_index(self, documents: list[dict]) -> int:
        """Batch index multiple documents.

        Each document should have 'id', 'text', and 'metadata' keys.

        Args:
            documents: List of document dicts.

        Returns:
            Number of documents indexed successfully.
        """
        if not self._available or self._client is None:
            logger.warning("EdgeQuake unavailable, skipping batch indexing")
            return 0

        count = 0
        for doc in documents:
            success = self.index_document(
                doc_id=doc.get("id", ""),
                text=doc.get("text", ""),
                metadata=doc.get("metadata", {}),
            )
            if success:
                count += 1

        logger.info("Batch indexed %d/%d documents", count, len(documents))
        return count

    def build_graph_index(self) -> bool:
        """Trigger EdgeQuake graph index rebuild.

        Returns:
            True if graph index build was triggered successfully.
        """
        if not self._available or self._client is None:
            logger.warning("EdgeQuake unavailable, skipping graph index build")
            return False

        try:
            response = self._client.post("/api/v1/index/build")  # type: ignore[union-attr]
            if response.status_code in (200, 202):
                logger.info("Graph index build triggered successfully")
                return True
            logger.warning("Failed to trigger graph index build: HTTP %d", response.status_code)
            return False
        except Exception as e:
            logger.error("Error triggering graph index build: %s", e)
            return False
