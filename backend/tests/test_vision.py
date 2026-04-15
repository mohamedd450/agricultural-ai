"""Tests for VisionService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.vision_service import DISEASE_CLASSES, DISEASE_LABELS, VisionService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def _mock_settings():
    """Patch get_settings so VisionService can be instantiated."""
    settings = MagicMock(
        vision_model_name="efficientnet_b0",
        vision_confidence_threshold=0.7,
    )
    with patch("app.services.vision_service.get_settings", return_value=settings):
        yield settings


@pytest.fixture
def vision_service(_mock_settings):
    """Return a VisionService running in fallback mode (no PyTorch)."""
    with (
        patch("app.services.vision_service._try_load_torch", return_value=(None, None, None)),
        patch("app.services.vision_service._try_load_pil", return_value=None),
    ):
        return VisionService()


@pytest.fixture
def vision_service_with_model(_mock_settings):
    """Return a VisionService with a mocked PyTorch model."""
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.no_grad.return_value.__enter__ = MagicMock()
    mock_torch.no_grad.return_value.__exit__ = MagicMock()

    mock_transforms = MagicMock()
    mock_models = MagicMock()

    # Build a fake softmax output
    fake_probs = MagicMock()
    fake_probs.shape = (1, 15)
    mock_torch.max.return_value = (
        MagicMock(item=MagicMock(return_value=0.92)),
        MagicMock(item=MagicMock(return_value=3)),
    )
    mock_torch.topk.return_value = (
        [[MagicMock(item=MagicMock(return_value=0.92))]],
        [[MagicMock(item=MagicMock(return_value=3))]],
    )
    mock_torch.nn.functional.softmax.return_value = fake_probs

    mock_model = MagicMock()
    mock_model.return_value = MagicMock()

    with (
        patch("app.services.vision_service._try_load_torch", return_value=(mock_torch, mock_transforms, mock_models)),
        patch("app.services.vision_service._try_load_pil", return_value=MagicMock()),
    ):
        svc = VisionService(model=mock_model)
        svc._torch = mock_torch
        return svc


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_image_returns_result(vision_service):
    """Fallback mode still returns a well-formed result dict."""
    result = await vision_service.analyze_image(b"\x89PNG fake image data")
    assert isinstance(result, dict)
    assert "class" in result
    assert "confidence" in result
    assert "label" in result
    assert result["class"] == "unknown"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_analyze_image_with_invalid_data(vision_service):
    """Empty/garbage bytes should not crash."""
    result = await vision_service.analyze_image(b"")
    assert isinstance(result, dict)
    assert result["class"] == "unknown"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_batch_analyze(vision_service):
    """batch_analyze returns one result per image."""
    images = [b"img1", b"img2", b"img3"]
    results = await vision_service.batch_analyze(images)
    assert len(results) == 3
    for r in results:
        assert isinstance(r, dict)
        assert "class" in r


def test_disease_classes_mapping():
    """DISEASE_CLASSES and DISEASE_LABELS should be consistent."""
    assert len(DISEASE_CLASSES) == 15
    for idx, class_name in DISEASE_CLASSES.items():
        assert isinstance(idx, int)
        assert isinstance(class_name, str)
        assert class_name in DISEASE_LABELS, f"{class_name} missing from DISEASE_LABELS"
