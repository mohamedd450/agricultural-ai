"""Embedding generation for agricultural text content."""

import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingsGenerator:
    """Generates vector embeddings for text using sentence-transformers or TF-IDF fallback."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        """Initialize the embeddings generator.

        Args:
            model_name: Name of the sentence-transformers model to use.
        """
        self._model_name = model_name
        self._model: Optional[object] = None
        self._cache: dict[str, list[float]] = {}
        self._use_fallback = False
        self._load_model()

    def _load_model(self) -> None:
        """Load the sentence-transformers model, falling back to TF-IDF."""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info("Loaded model: %s", self._model_name)
        except Exception as e:
            logger.warning("Failed to load sentence-transformers model: %s. Using TF-IDF fallback.", e)
            self._use_fallback = True

    def generate(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        embedding: list[float]
        if self._use_fallback:
            embedding = self._tfidf_embed([text])[0]
        else:
            try:
                result = self._model.encode([text])  # type: ignore[union-attr]
                embedding = result[0].tolist()
            except Exception as e:
                logger.error("Embedding generation failed: %s", e)
                embedding = self._tfidf_embed([text])[0]

        self._cache[cache_key] = embedding
        return embedding

    def batch_generate(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        uncached_indices: list[int] = []
        uncached_texts: list[str] = []
        results: list[Optional[list[float]]] = [None] * len(texts)

        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            if self._use_fallback:
                new_embeddings = self._tfidf_embed(uncached_texts)
            else:
                try:
                    encoded = self._model.encode(uncached_texts)  # type: ignore[union-attr]
                    new_embeddings = [e.tolist() for e in encoded]
                except Exception as e:
                    logger.error("Batch embedding failed: %s", e)
                    new_embeddings = self._tfidf_embed(uncached_texts)

            for idx, embedding in zip(uncached_indices, new_embeddings):
                self._cache[self._cache_key(texts[idx])] = embedding
                results[idx] = embedding

        return [r if r is not None else [] for r in results]

    @staticmethod
    def _tfidf_embed(texts: list[str]) -> list[list[float]]:
        """Fallback TF-IDF embedding generation.

        Args:
            texts: List of texts to embed.

        Returns:
            List of sparse embedding vectors.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np

            vectorizer = TfidfVectorizer(max_features=384)
            matrix = vectorizer.fit_transform(texts)
            embeddings: list[list[float]] = []
            for i in range(matrix.shape[0]):
                vec = matrix[i].toarray().flatten()
                padded = np.zeros(384)
                padded[: len(vec)] = vec
                norm = np.linalg.norm(padded)
                if norm > 0:
                    padded = padded / norm
                embeddings.append(padded.tolist())
            return embeddings
        except Exception as e:
            logger.error("TF-IDF fallback failed: %s", e)
            return [[0.0] * 384 for _ in texts]

    @staticmethod
    def _cache_key(text: str) -> str:
        """Generate a cache key for text.

        Args:
            text: Input text.

        Returns:
            SHA256 hex digest.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
