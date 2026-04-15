"""Tests for AgriOrchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrators.langgraph_orchestrator import AgriOrchestrator


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _patch_langgraph_unavailable():
    """Force the orchestrator into sequential-fallback mode."""
    return patch(
        "app.orchestrators.langgraph_orchestrator._LANGGRAPH_AVAILABLE", False
    )


def _mock_sequential_pipeline(final_response=None, errors=None):
    """Return a patch for _sequential_pipeline producing *final_response*."""
    async def _fake_pipeline(state):
        state["final_response"] = final_response or {
            "diagnosis": "Leaf Blight",
            "confidence": 0.82,
        }
        state["errors"] = errors or []
        return state

    return patch(
        "app.orchestrators.langgraph_orchestrator._sequential_pipeline",
        side_effect=_fake_pipeline,
    )


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_text_only_processing():
    """Process a text-only query without image/audio."""
    with _patch_langgraph_unavailable(), _mock_sequential_pipeline():
        orchestrator = AgriOrchestrator()
        result = await orchestrator.process(query="What is leaf blight?", language="en")

    assert isinstance(result, dict)
    assert "diagnosis" in result
    assert result["diagnosis"] == "Leaf Blight"
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_full_pipeline():
    """Process a request with query, image, and audio data."""
    response = {
        "diagnosis": "Powdery Mildew",
        "confidence": 0.91,
        "treatment": "Apply sulfur fungicide",
    }
    with _patch_langgraph_unavailable(), _mock_sequential_pipeline(final_response=response):
        orchestrator = AgriOrchestrator()
        result = await orchestrator.process(
            query="What disease?",
            image_data=b"fake-image",
            audio_data=b"fake-audio",
            language="ar",
        )

    assert result["diagnosis"] == "Powdery Mildew"
    assert result["confidence"] == 0.91


@pytest.mark.asyncio
async def test_error_handling():
    """The orchestrator should capture exceptions, not crash."""

    async def _exploding_pipeline(state):
        raise RuntimeError("Service unavailable")

    with (
        _patch_langgraph_unavailable(),
        patch(
            "app.orchestrators.langgraph_orchestrator._sequential_pipeline",
            side_effect=_exploding_pipeline,
        ),
    ):
        orchestrator = AgriOrchestrator()
        result = await orchestrator.process(query="boom")

    assert "errors" in result
    assert len(result["errors"]) > 0
    assert result["final_response"] is None
