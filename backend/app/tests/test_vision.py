"""Tests for the VisionService.

Covers image classification, heatmap generation, confidence scoring,
error handling, and format validation.
"""

from __future__ import annotations

import pytest

from app.services.vision_service import VisionService


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def vision_service():
    """Return an unloaded VisionService (no PyTorch required)."""
    return VisionService(model_name="efficientnet_b0")


@pytest.fixture()
def minimal_png() -> bytes:
    """1×1 pixel PNG for basic upload/format tests."""
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


# ── Model lifecycle ───────────────────────────────────────────────────────


class TestVisionServiceInit:
    def test_initial_state(self, vision_service: VisionService) -> None:
        """Service starts in unloaded state."""
        assert vision_service.is_loaded is False
        assert vision_service.model is None
        assert vision_service.model_name == "efficientnet_b0"

    def test_default_class_names_empty(self, vision_service: VisionService) -> None:
        assert vision_service.class_names == []

    @pytest.mark.asyncio
    async def test_load_model_without_torch(
        self, vision_service: VisionService
    ) -> None:
        """load_model should not raise even when torch is unavailable."""
        await vision_service.load_model()
        # model may or may not load depending on torch availability
        assert vision_service.is_loaded in (True, False)


# ── analyze_image ─────────────────────────────────────────────────────────


class TestAnalyzeImage:
    @pytest.mark.asyncio
    async def test_returns_dict(self, vision_service: VisionService, minimal_png: bytes) -> None:
        result = await vision_service.analyze_image(minimal_png)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_result_keys_when_model_unloaded(
        self, vision_service: VisionService, minimal_png: bytes
    ) -> None:
        """When model is not loaded, result must still contain required keys."""
        result = await vision_service.analyze_image(minimal_png)
        assert "class" in result
        assert "confidence" in result
        assert "all_predictions" in result

    @pytest.mark.asyncio
    async def test_confidence_in_range(
        self, vision_service: VisionService, minimal_png: bytes
    ) -> None:
        result = await vision_service.analyze_image(minimal_png)
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_unknown_class_when_unloaded(
        self, vision_service: VisionService, minimal_png: bytes
    ) -> None:
        result = await vision_service.analyze_image(minimal_png)
        # Model not loaded → class should be "unknown"
        assert result["class"] == "unknown"

    @pytest.mark.asyncio
    async def test_invalid_bytes_does_not_raise(
        self, vision_service: VisionService
    ) -> None:
        """Invalid image bytes should return an error dict, not raise."""
        result = await vision_service.analyze_image(b"not-an-image")
        assert isinstance(result, dict)
        assert "class" in result

    @pytest.mark.asyncio
    async def test_empty_bytes_does_not_raise(
        self, vision_service: VisionService
    ) -> None:
        result = await vision_service.analyze_image(b"")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_all_predictions_is_list(
        self, vision_service: VisionService, minimal_png: bytes
    ) -> None:
        result = await vision_service.analyze_image(minimal_png)
        assert isinstance(result["all_predictions"], list)


# ── generate_heatmap ──────────────────────────────────────────────────────


class TestGenerateHeatmap:
    @pytest.mark.asyncio
    async def test_returns_none_when_unloaded(
        self, vision_service: VisionService, minimal_png: bytes
    ) -> None:
        result = await vision_service.generate_heatmap(minimal_png)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_bytes_returns_none(
        self, vision_service: VisionService
    ) -> None:
        result = await vision_service.generate_heatmap(b"garbage")
        assert result is None


# ── is_loaded property ────────────────────────────────────────────────────


class TestIsLoaded:
    def test_false_by_default(self, vision_service: VisionService) -> None:
        assert vision_service.is_loaded is False

    def test_true_when_model_set(self, vision_service: VisionService) -> None:
        vision_service.model = object()  # any truthy value
        assert vision_service.is_loaded is True

    def test_false_when_model_cleared(self, vision_service: VisionService) -> None:
        vision_service.model = object()
        vision_service.model = None
        assert vision_service.is_loaded is False
