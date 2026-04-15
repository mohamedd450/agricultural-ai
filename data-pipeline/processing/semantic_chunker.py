from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Split text into overlapping, semantically coherent chunks."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        language: str = "ar",
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.language = language

    def chunk_text(
        self, text: str, metadata: dict | None = None
    ) -> list[dict]:
        """Split *text* into chunks with overlap.

        Returns a list of
        ``{"text": str, "metadata": dict, "chunk_index": int}``.
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        sentences = self._split_by_sentences(text)
        merged = self._merge_to_chunks(sentences)

        chunks: list[dict] = []
        for idx, chunk_text in enumerate(merged):
            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        **metadata,
                        "language": self.language,
                        "chunk_size": len(chunk_text),
                    },
                    "chunk_index": idx,
                }
            )

        logger.debug(
            "Created %d chunks (target size=%d, overlap=%d)",
            len(chunks),
            self.chunk_size,
            self.chunk_overlap,
        )
        return chunks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _split_by_sentences(self, text: str) -> list[str]:
        """Sentence-level splitting with support for Arabic punctuation."""
        # Arabic & Latin sentence-ending punctuation
        pattern = r"(?<=[.!?\u061F\u06D4])\s+"
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _merge_to_chunks(self, sentences: list[str]) -> list[str]:
        """Merge sentences into chunks of approximately *chunk_size* chars.

        Consecutive chunks share up to *chunk_overlap* characters so that
        context is preserved across boundaries.
        """
        if not sentences:
            return []

        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current and current_len + sentence_len + 1 > self.chunk_size:
                chunks.append(" ".join(current))

                # Build overlap from the tail of the current chunk
                overlap: list[str] = []
                overlap_len = 0
                for s in reversed(current):
                    if overlap_len + len(s) + 1 > self.chunk_overlap:
                        break
                    overlap.insert(0, s)
                    overlap_len += len(s) + 1

                current = overlap
                current_len = overlap_len

            current.append(sentence)
            current_len += sentence_len + 1

        if current:
            chunks.append(" ".join(current))

        return chunks
