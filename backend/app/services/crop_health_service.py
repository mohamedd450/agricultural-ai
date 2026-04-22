"""Crop health prediction service using a lightweight linear model."""

from __future__ import annotations

import math

from app.utils.exceptions import InvalidInputError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CropHealthService:
    """Predict crop health risk from agronomic and field-observation features."""

    _WEIGHTS: dict[str, float] = {
        "soil_moisture": -0.02,
        "temperature_c": 0.08,
        "humidity": 0.03,
        "rainfall_mm_7d": -0.01,
        "leaf_discoloration": 0.7,
        "pest_activity": 0.6,
    }
    _BIAS: float = -1.4

    async def predict_health(self, features: dict[str, float]) -> dict:
        """Return crop health prediction from normalized tabular features."""
        missing = [name for name in self._WEIGHTS if name not in features]
        if missing:
            raise InvalidInputError(
                message="Missing required crop health features.",
                error_code="CROP_FEATURES_MISSING",
                details={"missing_features": missing},
            )

        linear_score = self._BIAS
        for name, weight in self._WEIGHTS.items():
            linear_score += weight * float(features[name])

        risk_score = 1.0 / (1.0 + math.exp(-linear_score))
        if risk_score >= 0.75:
            health_status = "critical"
        elif risk_score >= 0.45:
            health_status = "at_risk"
        else:
            health_status = "healthy"

        recommendations: list[str] = []
        if float(features.get("leaf_discoloration", 0.0)) >= 0.5:
            recommendations.append("Inspect crops for nutrient deficiency and fungal stress.")
        if float(features.get("pest_activity", 0.0)) >= 0.5:
            recommendations.append("Apply integrated pest-management scouting this week.")
        if float(features.get("soil_moisture", 0.0)) < 30:
            recommendations.append("Increase irrigation frequency to improve soil moisture.")

        if not recommendations:
            recommendations.append("Maintain current irrigation and monitoring schedule.")

        logger.info(
            "Crop health predicted: status=%s risk_score=%.3f",
            health_status,
            risk_score,
        )
        return {
            "health_status": health_status,
            "risk_score": round(risk_score, 4),
            "confidence": round(self._calculate_confidence(risk_score), 4),
            "recommendations": recommendations,
            "factors": features,
        }

    @staticmethod
    def _calculate_confidence(risk_score: float) -> float:
        """Map risk probability distance from decision boundary (0.5) to 0-1 confidence."""
        return abs(risk_score - 0.5) * 2
