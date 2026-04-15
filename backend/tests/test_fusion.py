"""Tests for FusionService."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.fusion_service import FusionService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

VISION_HIGH = {
    "class": "leaf_blight",
    "confidence": 0.92,
    "label": "Leaf Blight",
    "features": {"output_mean": 0.1},
    "all_predictions": [
        {"class": "leaf_blight", "confidence": 0.92},
        {"class": "rust", "confidence": 0.04},
    ],
}

GRAPH_HIGH = {
    "answer": "Leaf blight caused by fungi. Apply copper fungicide.",
    "confidence": 0.80,
    "graph_paths": ["Leaf Blight -> treated_by -> Copper Fungicide"],
    "reasoning_steps": [
        "Identified disease: Leaf Blight",
        "Found treatment: copper fungicide",
    ],
}

VECTOR_RESULTS = [
    {"score": 0.88, "payload": {"diagnosis": "Leaf Blight", "treatment": "Remove infected leaves"}},
    {"score": 0.72, "payload": {"diagnosis": "Early Blight", "treatment": "Apply fungicide"}},
]


@pytest.fixture
def _mock_settings():
    settings = MagicMock(
        vision_model_name="efficientnet_b0",
        vision_confidence_threshold=0.7,
        edgequake_host="localhost",
        edgequake_port=9090,
    )
    with patch("app.services.fusion_service.get_settings", return_value=settings):
        with patch("app.services.decision_router.get_settings", return_value=settings):
            yield settings


@pytest.fixture
def fusion_service(_mock_settings):
    return FusionService()


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fuse_all_sources(fusion_service):
    """Fusion with all three sources present produces a valid response."""
    result = await fusion_service.fuse(VISION_HIGH, GRAPH_HIGH, VECTOR_RESULTS)
    assert isinstance(result, dict)
    assert "diagnosis" in result
    assert "confidence" in result
    assert "treatment" in result
    assert "explanation" in result
    assert "sources" in result
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_fuse_partial_sources(fusion_service):
    """Fusion still works when graph and vector results are empty."""
    empty_graph = {"answer": "", "confidence": 0.0, "graph_paths": [], "reasoning_steps": []}
    result = await fusion_service.fuse(VISION_HIGH, empty_graph, [])
    assert isinstance(result, dict)
    assert "diagnosis" in result
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_confidence_calculation(fusion_service):
    """Confidence in the fused result should be between 0 and 1."""
    result = await fusion_service.fuse(VISION_HIGH, GRAPH_HIGH, VECTOR_RESULTS)
    assert 0.0 <= result["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_explanation_generation(fusion_service):
    """Explanation should mention the analysis sources."""
    result = await fusion_service.fuse(
        VISION_HIGH,
        GRAPH_HIGH,
        VECTOR_RESULTS,
        user_context={"language": "en"},
    )
    explanation = result.get("explanation", "")
    assert len(explanation) > 0
    # Should reference at least vision or graph analysis
    assert "confidence" in explanation.lower() or "analysis" in explanation.lower() or "image" in explanation.lower()
