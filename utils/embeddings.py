from __future__ import annotations

import hashlib
from typing import Iterable

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None


class EmbeddingModel:
    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        self._model = SentenceTransformer(model_name) if SentenceTransformer else None

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        text_list = list(texts)
        if self._model is not None:
            vectors = self._model.encode(text_list, normalize_embeddings=True)
            return [list(map(float, row)) for row in vectors]
        vectors: list[list[float]] = []
        for text in text_list:
            digest = hashlib.sha256(text.encode("utf-8")).digest()[:16]
            vectors.append([byte / 255.0 for byte in digest])
        return vectors
