"""Computer-vision service for crop disease detection and image analysis."""

from __future__ import annotations

import io
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import torch
    import torchvision.models as models
    import torchvision.transforms as transforms
    from PIL import Image

    VISION_DEPS_AVAILABLE = True
except ImportError:  # pragma: no cover
    VISION_DEPS_AVAILABLE = False
    logger.warning(
        "torch / torchvision / Pillow not installed – VisionService will be "
        "non-functional. Install them to enable image analysis."
    )


class VisionService:
    """Analyse agricultural images using a pre-trained EfficientNet backbone."""

    def __init__(self, model_name: str = "efficientnet_b0") -> None:
        self.model_name = model_name
        self.model: Optional[object] = None
        self.transforms: Optional[object] = None
        self.class_names: list[str] = []  # to be loaded later

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    async def load_model(self) -> None:
        """Load the EfficientNet model and prepare image transforms."""
        if not VISION_DEPS_AVAILABLE:
            logger.warning("Vision dependencies unavailable – skipping model load")
            return

        try:
            model_factory = getattr(models, self.model_name, None)
            if model_factory is None:
                logger.warning(
                    "Model '%s' not found in torchvision.models", self.model_name
                )
                return

            self.model = model_factory(weights=None)
            self.model.eval()  # type: ignore[union-attr]

            self.transforms = transforms.Compose(
                [
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                ]
            )

            logger.info("Vision model '%s' loaded successfully", self.model_name)
        except Exception:
            logger.warning(
                "Failed to load vision model '%s' – service will be degraded",
                self.model_name,
                exc_info=True,
            )
            self.model = None

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    async def analyze_image(self, image_data: bytes) -> dict:
        """Run classification on raw image bytes.

        Returns
        -------
        dict
            ``{"class": str, "confidence": float, "all_predictions": list[dict]}``
        """
        if self.model is None:
            return {
                "class": "unknown",
                "confidence": 0.0,
                "all_predictions": [],
                "message": "Model not loaded",
            }

        try:
            tensor = self._preprocess_image(image_data)

            with torch.no_grad():
                outputs = self.model(tensor)  # type: ignore[misc]
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

            top_k = min(5, len(probabilities))
            values, indices = torch.topk(probabilities, top_k)

            all_predictions: list[dict] = []
            for prob, idx in zip(values.tolist(), indices.tolist()):
                class_name = (
                    self.class_names[idx]
                    if idx < len(self.class_names)
                    else f"class_{idx}"
                )
                all_predictions.append(
                    {"class": class_name, "confidence": round(prob, 4)}
                )

            top = (
                all_predictions[0]
                if all_predictions
                else {"class": "unknown", "confidence": 0.0}
            )

            return {
                "class": top["class"],
                "confidence": top["confidence"],
                "all_predictions": all_predictions,
            }
        except Exception:
            logger.error("Image analysis failed", exc_info=True)
            return {
                "class": "error",
                "confidence": 0.0,
                "all_predictions": [],
                "message": "Analysis failed",
            }

    async def generate_heatmap(self, image_data: bytes) -> Optional[bytes]:
        """Generate a Grad-CAM-style activation heatmap for the image."""
        if not VISION_DEPS_AVAILABLE or self.model is None:
            return None

        try:
            import numpy as np

            tensor = self._preprocess_image(image_data)
            tensor.requires_grad_(True)

            # Forward pass
            output = self.model(tensor)  # type: ignore[misc]
            class_idx = output.argmax(dim=1).item()
            score = output[0, class_idx]

            # Backward pass
            self.model.zero_grad()  # type: ignore[union-attr]
            score.backward()

            gradients = tensor.grad
            if gradients is None:
                return None

            heatmap = gradients.abs().mean(dim=1).squeeze().numpy()

            # Normalise to 0-255
            heatmap = heatmap - heatmap.min()
            denom = heatmap.max()
            if denom > 0:
                heatmap = heatmap / denom
            heatmap = (heatmap * 255).astype(np.uint8)

            heatmap_image = Image.fromarray(heatmap, mode="L")
            heatmap_image = heatmap_image.resize((224, 224))

            buffer = io.BytesIO()
            heatmap_image.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception:
            logger.error("Heatmap generation failed", exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _preprocess_image(self, image_data: bytes) -> torch.Tensor:
        """Open raw bytes as a PIL image and apply the model transforms."""
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        tensor: torch.Tensor = self.transforms(image)  # type: ignore[misc]
        return tensor.unsqueeze(0)

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` when the underlying model is ready for inference."""
        return self.model is not None
