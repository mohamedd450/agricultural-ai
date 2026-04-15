"""Semantic text chunking for agricultural documents."""

import logging
import re
import uuid

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Splits text into semantically coherent chunks."""

    def chunk(
        self, text: str, max_chunk_size: int = 512, overlap: int = 50
    ) -> list[dict]:
        """Split text into overlapping semantic chunks.

        Args:
            text: Input text to chunk.
            max_chunk_size: Maximum characters per chunk.
            overlap: Number of overlapping characters between chunks.

        Returns:
            List of chunk dicts with keys: text, start_idx, end_idx, chunk_id, metadata.
        """
        if not text.strip():
            return []

        paragraphs = self._split_paragraphs(text)
        chunks: list[dict] = []
        current_chunk = ""
        current_start = 0
        text_pos = 0

        for paragraph in paragraphs:
            para_start = text.find(paragraph, text_pos)
            if para_start == -1:
                para_start = text_pos

            if len(current_chunk) + len(paragraph) + 1 <= max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_start = para_start
            else:
                if current_chunk:
                    chunks.append(self._make_chunk(
                        current_chunk, current_start, current_start + len(current_chunk)
                    ))
                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + "\n\n" + paragraph
                    current_start = para_start - len(overlap_text)
                else:
                    current_chunk = paragraph
                    current_start = para_start

                # Handle paragraphs longer than max_chunk_size
                while len(current_chunk) > max_chunk_size:
                    split_point = self._find_sentence_boundary(
                        current_chunk, max_chunk_size
                    )
                    chunks.append(self._make_chunk(
                        current_chunk[:split_point],
                        current_start,
                        current_start + split_point,
                    ))
                    current_start += split_point - overlap
                    current_chunk = current_chunk[split_point - overlap:]

            text_pos = para_start + len(paragraph)

        if current_chunk.strip():
            chunks.append(self._make_chunk(
                current_chunk, current_start, current_start + len(current_chunk)
            ))

        return chunks

    @staticmethod
    def _split_paragraphs(text: str) -> list[str]:
        """Split text into paragraphs.

        Args:
            text: Input text.

        Returns:
            List of non-empty paragraph strings.
        """
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    @staticmethod
    def _find_sentence_boundary(text: str, max_pos: int) -> int:
        """Find the best sentence boundary before max_pos.

        Handles both Arabic and English sentence endings.

        Args:
            text: Input text.
            max_pos: Maximum position to search.

        Returns:
            Position of best split point.
        """
        # Look for sentence-ending punctuation
        search_text = text[:max_pos]
        for pattern in [r"[.!?؟।]\s", r"[،,;:]\s", r"\s"]:
            matches = list(re.finditer(pattern, search_text))
            if matches:
                return matches[-1].end()
        return max_pos

    @staticmethod
    def _make_chunk(text: str, start_idx: int, end_idx: int) -> dict:
        """Create a chunk dictionary.

        Args:
            text: Chunk text content.
            start_idx: Start index in original text.
            end_idx: End index in original text.

        Returns:
            Chunk dict with text, indices, id, and metadata.
        """
        return {
            "text": text.strip(),
            "start_idx": max(0, start_idx),
            "end_idx": end_idx,
            "chunk_id": str(uuid.uuid4()),
            "metadata": {
                "char_count": len(text.strip()),
                "word_count": len(text.split()),
            },
        }
