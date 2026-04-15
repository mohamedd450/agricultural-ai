"""Tests for the LangGraph orchestrator.

Covers workflow creation, process method, routing logic, sequential
fallback, and error handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrators.langgraph_orchestrator import LangGraphOrchestrator


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def orchestrator():
    """Return an orchestrator (may use sequential fallback if LangGraph absent)."""
    return LangGraphOrchestrator()


@pytest.fixture()
def minimal_image_input(sample_image_bytes):
    return {
        "image_data": sample_image_bytes,
        "text_query": "ما مشكلة النبتة؟",
        "language": "ar",
        "session_id": "test-session-001",
    }


@pytest.fixture()
def text_only_input():
    return {
        "text_query": "كيف أعالج نقص النيتروجين؟",
        "language": "ar",
        "session_id": "test-session-002",
    }


# ── Init ──────────────────────────────────────────────────────────────────


class TestOrchestratorInit:
    def test_creates_instance(self, orchestrator: LangGraphOrchestrator) -> None:
        assert orchestrator is not None

    def test_has_workflow_or_none(
        self, orchestrator: LangGraphOrchestrator
    ) -> None:
        # _workflow is either compiled or None
        assert orchestrator._workflow is None or hasattr(
            orchestrator._workflow, "ainvoke"
        )


# ── process ───────────────────────────────────────────────────────────────


class TestProcess:
    @pytest.mark.asyncio
    async def test_returns_dict(
        self, orchestrator: LangGraphOrchestrator, text_only_input: dict
    ) -> None:
        result = await orchestrator.process(text_only_input)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_empty_input_returns_dict(
        self, orchestrator: LangGraphOrchestrator
    ) -> None:
        result = await orchestrator.process({})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_result_has_content_or_error(
        self, orchestrator: LangGraphOrchestrator, text_only_input: dict
    ) -> None:
        result = await orchestrator.process(text_only_input)
        # Must have either a diagnosis or an error key
        has_content = "diagnosis" in result or "error" in result
        assert has_content

    @pytest.mark.asyncio
    async def test_image_input_does_not_raise(
        self, orchestrator: LangGraphOrchestrator, minimal_image_input: dict
    ) -> None:
        result = await orchestrator.process(minimal_image_input)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_language_ar_passed_through(
        self, orchestrator: LangGraphOrchestrator
    ) -> None:
        result = await orchestrator.process(
            {"text_query": "test", "language": "ar"}
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_language_en_passed_through(
        self, orchestrator: LangGraphOrchestrator
    ) -> None:
        result = await orchestrator.process(
            {"text_query": "test", "language": "en"}
        )
        assert isinstance(result, dict)


# ── _route_by_input_type ──────────────────────────────────────────────────


class TestRoutingLogic:
    def test_image_routes_to_vision(self) -> None:
        state = {"input_type": "image"}
        result = LangGraphOrchestrator._route_by_input_type(state)
        assert result == "vision_agent"

    def test_voice_routes_to_voice(self) -> None:
        state = {"input_type": "voice"}
        result = LangGraphOrchestrator._route_by_input_type(state)
        assert result == "voice_agent"

    def test_text_routes_to_edgequake(self) -> None:
        state = {"input_type": "text"}
        result = LangGraphOrchestrator._route_by_input_type(state)
        assert result == "edgequake_agent"

    def test_unknown_type_routes_to_edgequake(self) -> None:
        state = {"input_type": "unknown"}
        result = LangGraphOrchestrator._route_by_input_type(state)
        assert result == "edgequake_agent"

    def test_missing_type_routes_to_edgequake(self) -> None:
        state: dict = {}
        result = LangGraphOrchestrator._route_by_input_type(state)
        assert result == "edgequake_agent"


# ── Sequential fallback ───────────────────────────────────────────────────


class TestSequentialFallback:
    @pytest.mark.asyncio
    async def test_fallback_returns_dict(
        self, orchestrator: LangGraphOrchestrator
    ) -> None:
        state = {
            "input_type": "",
            "text_query": "test",
            "image_data": None,
            "audio_data": None,
            "language": "ar",
            "session_id": "test",
            "vision_result": None,
            "voice_result": None,
            "graph_rag_result": None,
            "vector_result": None,
            "routing_decision": None,
            "fused_result": None,
            "final_response": None,
            "error": None,
        }
        result = await orchestrator._simple_sequential_process(state)
        assert isinstance(result, dict)
