"""Tests for the GraphRAGService.

Covers graph query, multi-hop reasoning, confidence scoring,
fallback responses, and error handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.graph_rag_service import GraphRAGService


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def graph_rag_service():
    """Return a GraphRAGService with no active HTTP session."""
    return GraphRAGService(endpoint="http://localhost:8081")


@pytest.fixture()
def graph_rag_with_session():
    """Return a GraphRAGService with a mock HTTP session."""
    svc = GraphRAGService(endpoint="http://localhost:8081")
    svc.session = MagicMock()
    return svc


def _make_response(data: dict, status: int = 200):
    """Build a mock aiohttp response."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    resp.raise_for_status = MagicMock()
    return resp


# ── Init ──────────────────────────────────────────────────────────────────


class TestGraphRAGServiceInit:
    def test_default_endpoint(self, graph_rag_service: GraphRAGService) -> None:
        assert "8081" in graph_rag_service.endpoint

    def test_session_none_initially(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        assert graph_rag_service.session is None

    def test_is_available_false_without_session(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        assert graph_rag_service.is_available is False

    def test_is_available_true_with_session(
        self, graph_rag_with_session: GraphRAGService
    ) -> None:
        assert graph_rag_with_session.is_available is True


# ── query ─────────────────────────────────────────────────────────────────


class TestQuery:
    @pytest.mark.asyncio
    async def test_fallback_when_no_session(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        result = await graph_rag_service.query("ما مشكلة النبتة؟")
        assert result["answer"] == ""
        assert result["confidence"] == 0.0
        assert result["graph_paths"] == []

    @pytest.mark.asyncio
    async def test_returns_required_keys(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        result = await graph_rag_service.query("test")
        assert "answer" in result
        assert "confidence" in result
        assert "graph_paths" in result
        assert "reasoning_steps" in result

    @pytest.mark.asyncio
    async def test_with_mock_session_success(
        self, graph_rag_with_session: GraphRAGService
    ) -> None:
        edge_response = {
            "answer": "نقص النيتروجين",
            "confidence": 0.82,
            "graph_paths": ["أوراق صفراء → نقص النيتروجين → اليوريا"],
            "reasoning_steps": ["step1"],
        }
        mock_resp = _make_response(edge_response)
        graph_rag_with_session.session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_resp),
                __aexit__=AsyncMock(return_value=False),
            )
        )

        result = await graph_rag_with_session.query("ما مشكلة النبتة؟")
        assert result["answer"] == "نقص النيتروجين"
        assert result["confidence"] == 0.82

    @pytest.mark.asyncio
    async def test_fallback_on_session_error(
        self, graph_rag_with_session: GraphRAGService
    ) -> None:
        graph_rag_with_session.session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(side_effect=ConnectionError("timeout")),
                __aexit__=AsyncMock(return_value=False),
            )
        )
        result = await graph_rag_with_session.query("test")
        assert result["answer"] == ""
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_arabic_language_param(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        result = await graph_rag_service.query("test", language="ar")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_with_context(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        ctx = {"vision_class": "nitrogen_deficiency", "confidence": 0.91}
        result = await graph_rag_service.query("test", context=ctx)
        assert isinstance(result, dict)


# ── multi_hop_reasoning ───────────────────────────────────────────────────


class TestMultiHopReasoning:
    @pytest.mark.asyncio
    async def test_fallback_when_no_session(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        result = await graph_rag_service.multi_hop_reasoning("test", max_hops=3)
        assert result["answer"] == ""
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_returns_paths_key(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        result = await graph_rag_service.multi_hop_reasoning("test")
        assert "paths" in result

    @pytest.mark.asyncio
    async def test_max_hops_parameter_accepted(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        # Just ensure no TypeError
        result = await graph_rag_service.multi_hop_reasoning("test", max_hops=5)
        assert isinstance(result, dict)


# ── lifecycle ─────────────────────────────────────────────────────────────


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_close_when_no_session(
        self, graph_rag_service: GraphRAGService
    ) -> None:
        """Closing with no session should not raise."""
        await graph_rag_service.close()

    @pytest.mark.asyncio
    async def test_close_with_mock_session(
        self, graph_rag_with_session: GraphRAGService
    ) -> None:
        graph_rag_with_session.session.close = AsyncMock()
        await graph_rag_with_session.close()
        assert graph_rag_with_session.session is None
