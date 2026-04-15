"""Tests for the FusionService.

Covers result merging, confidence weighting, multi-source fusion,
and empty/None input handling.
"""

from __future__ import annotations

import pytest

from app.services.fusion_service import FusionService


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def fusion_service():
    return FusionService()


@pytest.fixture()
def vision_result():
    return {
        "class": "nitrogen_deficiency",
        "diagnosis": "نقص النيتروجين",
        "treatment": "اليوريا",
        "confidence": 0.91,
        "graph_paths": [],
    }


@pytest.fixture()
def graph_rag_result():
    return {
        "answer": "نقص النيتروجين – يُنصح باستخدام اليوريا",
        "diagnosis": "نقص النيتروجين",
        "treatment": "اليوريا 46%",
        "confidence": 0.82,
        "graph_paths": ["أوراق صفراء → نقص النيتروجين → اليوريا"],
    }


@pytest.fixture()
def vector_result():
    return {
        "results": [{"text": "Nitrogen deficiency.", "score": 0.85}],
        "diagnosis": "Nitrogen deficiency",
        "treatment": "Apply urea",
        "confidence": 0.85,
        "graph_paths": [],
    }


@pytest.fixture()
def routing_vision_primary():
    return {
        "strategy": "vision_primary",
        "primary_source": "vision",
        "confidence": 0.91,
        "reasoning": "High vision confidence",
    }


@pytest.fixture()
def routing_graph_primary():
    return {
        "strategy": "graph_primary",
        "primary_source": "graph_rag",
        "confidence": 0.82,
        "reasoning": "High graph confidence",
    }


@pytest.fixture()
def routing_fusion():
    return {
        "strategy": "fusion",
        "primary_source": "combined",
        "confidence": 0.75,
        "reasoning": "No single source above threshold",
    }


# ── fuse – return shape ───────────────────────────────────────────────────


class TestFuseReturnShape:
    @pytest.mark.asyncio
    async def test_returns_dict(self, fusion_service: FusionService) -> None:
        result = await fusion_service.fuse()
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_required_keys_present(
        self, fusion_service: FusionService
    ) -> None:
        result = await fusion_service.fuse()
        for key in (
            "diagnosis", "treatment", "confidence",
            "graph_paths", "explanation", "source",
            "language", "timestamp"
        ):
            assert key in result, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_confidence_in_range(
        self, fusion_service: FusionService, vision_result, graph_rag_result
    ) -> None:
        result = await fusion_service.fuse(
            vision_result=vision_result,
            graph_rag_result=graph_rag_result,
        )
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_graph_paths_is_list(
        self, fusion_service: FusionService, graph_rag_result
    ) -> None:
        result = await fusion_service.fuse(graph_rag_result=graph_rag_result)
        assert isinstance(result["graph_paths"], list)


# ── Confidence weighting ──────────────────────────────────────────────────


class TestConfidenceWeighting:
    @pytest.mark.asyncio
    async def test_vision_weight_0_3(
        self, fusion_service: FusionService
    ) -> None:
        assert fusion_service.VISION_WEIGHT == pytest.approx(0.3)

    @pytest.mark.asyncio
    async def test_graph_rag_weight_0_4(
        self, fusion_service: FusionService
    ) -> None:
        assert fusion_service.GRAPH_RAG_WEIGHT == pytest.approx(0.4)

    @pytest.mark.asyncio
    async def test_vector_db_weight_0_3(
        self, fusion_service: FusionService
    ) -> None:
        assert fusion_service.VECTOR_DB_WEIGHT == pytest.approx(0.3)

    @pytest.mark.asyncio
    async def test_weights_sum_to_one(self, fusion_service: FusionService) -> None:
        total = (
            fusion_service.VISION_WEIGHT
            + fusion_service.GRAPH_RAG_WEIGHT
            + fusion_service.VECTOR_DB_WEIGHT
        )
        assert total == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_fused_score_calculation(
        self,
        fusion_service: FusionService,
        vision_result,
        graph_rag_result,
        vector_result,
    ) -> None:
        expected = (
            0.91 * 0.3 + 0.82 * 0.4 + 0.85 * 0.3
        )
        result = await fusion_service.fuse(
            vision_result=vision_result,
            graph_rag_result=graph_rag_result,
            vector_result=vector_result,
        )
        assert result["confidence"] == pytest.approx(expected, abs=0.01)


# ── Strategy selection ────────────────────────────────────────────────────


class TestStrategySelection:
    @pytest.mark.asyncio
    async def test_vision_primary_uses_vision_diagnosis(
        self,
        fusion_service: FusionService,
        vision_result,
        graph_rag_result,
        routing_vision_primary,
    ) -> None:
        result = await fusion_service.fuse(
            vision_result=vision_result,
            graph_rag_result=graph_rag_result,
            routing_decision=routing_vision_primary,
        )
        assert result["diagnosis"] == vision_result["diagnosis"]
        assert result["source"] == "vision"

    @pytest.mark.asyncio
    async def test_graph_primary_uses_graph_diagnosis(
        self,
        fusion_service: FusionService,
        vision_result,
        graph_rag_result,
        routing_graph_primary,
    ) -> None:
        result = await fusion_service.fuse(
            vision_result=vision_result,
            graph_rag_result=graph_rag_result,
            routing_decision=routing_graph_primary,
        )
        assert result["source"] == "graph_rag"

    @pytest.mark.asyncio
    async def test_fusion_strategy_source_combined(
        self,
        fusion_service: FusionService,
        vision_result,
        graph_rag_result,
        vector_result,
        routing_fusion,
    ) -> None:
        result = await fusion_service.fuse(
            vision_result=vision_result,
            graph_rag_result=graph_rag_result,
            vector_result=vector_result,
            routing_decision=routing_fusion,
        )
        assert result["source"] == "combined"


# ── Edge cases ────────────────────────────────────────────────────────────


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_all_none_inputs(self, fusion_service: FusionService) -> None:
        result = await fusion_service.fuse(
            vision_result=None,
            graph_rag_result=None,
            vector_result=None,
        )
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_no_routing_decision(
        self, fusion_service: FusionService, vision_result
    ) -> None:
        result = await fusion_service.fuse(
            vision_result=vision_result,
            routing_decision=None,
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_arabic_language(
        self, fusion_service: FusionService, vision_result
    ) -> None:
        result = await fusion_service.fuse(
            vision_result=vision_result, language="ar"
        )
        assert result["language"] == "ar"

    @pytest.mark.asyncio
    async def test_english_language(
        self, fusion_service: FusionService, vision_result
    ) -> None:
        result = await fusion_service.fuse(
            vision_result=vision_result, language="en"
        )
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_graph_paths_merged(
        self,
        fusion_service: FusionService,
        graph_rag_result,
        vector_result,
    ) -> None:
        graph_rag_result["graph_paths"] = ["path_a → path_b"]
        vector_result["graph_paths"] = ["path_c → path_d"]
        result = await fusion_service.fuse(
            graph_rag_result=graph_rag_result,
            vector_result=vector_result,
        )
        assert len(result["graph_paths"]) >= 1
