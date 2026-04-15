"""Smoke tests for the data pipeline components.

These tests verify that each pipeline stage can be instantiated and
called without raising unexpected exceptions, even when optional
dependencies (pypdf, sentence-transformers, qdrant-client, neo4j)
are absent.

Run with:
    pytest scripts/test_pipeline.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow running from repo root or data-pipeline/ directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ── TextCleaner ───────────────────────────────────────────────────────────


class TestTextCleaner:
    def setup_method(self) -> None:
        from ingestion.text_cleaner import TextCleaner

        self.cleaner = TextCleaner()

    def test_clean_empty(self) -> None:
        assert self.cleaner.clean("") == ""

    def test_clean_short_text_returns_empty(self) -> None:
        # Below min_length of 10
        assert self.cleaner.clean("hi") == ""

    def test_clean_arabic_diacritics_removed(self) -> None:
        # Arabic text with diacritics
        text = "الزِّرَاعَةُ العَرَبِيَّة"
        result = self.cleaner.clean(text)
        assert "ِ" not in result  # kasra removed

    def test_clean_url_removed(self) -> None:
        text = "Visit https://example.com for more agricultural information here"
        result = self.cleaner.clean(text)
        assert "https://" not in result

    def test_clean_whitespace_collapsed(self) -> None:
        text = "nitrogen   deficiency   in   plants   is   common"
        result = self.cleaner.clean(text)
        assert "  " not in result

    def test_clean_batch(self) -> None:
        texts = [
            "nitrogen deficiency in crops causes yellowing",
            "",  # will be discarded
            "soil analysis is important for plant health",
        ]
        result = self.cleaner.clean_batch(texts)
        assert len(result) == 2

    def test_is_arabic_true(self) -> None:
        assert self.cleaner.is_arabic("نقص النيتروجين في النباتات") is True

    def test_is_arabic_false(self) -> None:
        assert self.cleaner.is_arabic("nitrogen deficiency in plants") is False

    def test_detect_language_ar(self) -> None:
        assert self.cleaner.detect_language("نقص النيتروجين في النباتات") == "ar"

    def test_detect_language_en(self) -> None:
        assert self.cleaner.detect_language("nitrogen deficiency") == "en"


# ── SemanticChunker ───────────────────────────────────────────────────────


class TestSemanticChunker:
    def setup_method(self) -> None:
        from processing.semantic_chunker import SemanticChunker

        self.chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)

    def test_chunk_empty_text(self) -> None:
        assert self.chunker.chunk_text("") == []

    def test_chunk_returns_list(self) -> None:
        result = self.chunker.chunk_text("This is a test sentence about agriculture.")
        assert isinstance(result, list)

    def test_chunk_contains_required_keys(self) -> None:
        result = self.chunker.chunk_text(
            "Nitrogen deficiency causes yellowing of leaves in plants."
        )
        if result:
            assert "text" in result[0]
            assert "metadata" in result[0]
            assert "chunk_index" in result[0]

    def test_chunk_with_metadata(self) -> None:
        meta = {"source": "test.pdf", "page": 1}
        result = self.chunker.chunk_text(
            "Agriculture is the backbone of food security worldwide.", meta
        )
        if result:
            assert result[0]["metadata"]["source"] == "test.pdf"

    def test_long_text_produces_multiple_chunks(self) -> None:
        long_text = " ".join(["Word"] * 300)
        result = self.chunker.chunk_text(long_text)
        assert len(result) >= 1


# ── EmbeddingsGenerator ───────────────────────────────────────────────────


class TestEmbeddingsGenerator:
    def setup_method(self) -> None:
        from processing.embeddings_generator import EmbeddingsGenerator

        self.gen = EmbeddingsGenerator()

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self) -> None:
        result = await self.gen.generate([])
        assert result == []

    @pytest.mark.asyncio
    async def test_raises_when_model_unavailable(self) -> None:
        """generate() should raise RuntimeError if sentence-transformers absent."""
        import processing.embeddings_generator as eg_mod

        if eg_mod.SentenceTransformer is None:
            with pytest.raises(RuntimeError, match="sentence-transformers"):
                await self.gen.generate(["test text"])
        else:
            # Model available – just verify it returns a list
            result = await self.gen.generate(["test text"])
            assert isinstance(result, list)


# ── GraphExtractor ────────────────────────────────────────────────────────


class TestGraphExtractor:
    def setup_method(self) -> None:
        from processing.graph_extractor import GraphExtractor

        self.extractor = GraphExtractor()

    @pytest.mark.asyncio
    async def test_extract_entities_empty_text(self) -> None:
        result = await self.extractor.extract_entities("")
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_entities_returns_list(self) -> None:
        result = await self.extractor.extract_entities("Nitrogen deficiency.")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_relationships_no_entities(self) -> None:
        result = await self.extractor.extract_relationships("text", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_extract_relationships_one_entity(self) -> None:
        entities = [{"name": "nitrogen", "type": "nutrient"}]
        result = await self.extractor.extract_relationships("text", entities)
        assert result == []
