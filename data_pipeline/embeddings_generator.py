from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment, misc]

# NOTE: EmbedAnything integration is planned as a future enhancement.
# When available it will provide faster, Rust-backed embedding generation.


class EmbeddingsGenerator:
    """Generate vector embeddings for text using sentence-transformers."""

    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        self.model_name = model_name
        self._model = None

        if SentenceTransformer is None:
            logger.warning(
                "sentence-transformers is not installed. "
                "Embedding generation will not be available."
            )

    def _load_model(self) -> None:
        """Lazy-load the embedding model on first use."""
        if self._model is not None:
            return
        if SentenceTransformer is None:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            )
        logger.info("Loading embedding model: %s", self.model_name)
        self._model = SentenceTransformer(self.model_name)

    async def generate(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Returns a list of float vectors, one per input text.
        """
        if not texts:
            return []

        self._load_model()

        try:
            embeddings = self._model.encode(texts, show_progress_bar=False)
            return [vec.tolist() for vec in embeddings]
        except Exception:
            logger.exception("Embedding generation failed")
            raise

    async def generate_single(self, text: str) -> list[float]:
        """Generate an embedding for a single text string."""
        results = await self.generate([text])
        return results[0]
