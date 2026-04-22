"""Soil nutrient analysis utilities."""

from __future__ import annotations

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SoilAnalysisService:
    """Analyze soil nutrient readings and return agronomic recommendations."""

    async def analyze(self, samples: dict[str, float]) -> dict:
        """Evaluate nutrient ranges and produce soil health recommendations."""
        nitrogen = float(samples["nitrogen"])
        phosphorus = float(samples["phosphorus"])
        potassium = float(samples["potassium"])
        ph = float(samples["ph"])
        moisture = float(samples["moisture"])

        nutrient_levels = {
            "nitrogen": self._classify_range(nitrogen, low=20, high=50),
            "phosphorus": self._classify_range(phosphorus, low=15, high=40),
            "potassium": self._classify_range(potassium, low=120, high=250),
            "ph": self._classify_range(ph, low=6.0, high=7.5),
            "moisture": self._classify_range(moisture, low=25, high=60),
        }

        deficiencies = [name for name, status in nutrient_levels.items() if status == "low"]
        excesses = [name for name, status in nutrient_levels.items() if status == "high"]
        recommendations: list[str] = []

        if "nitrogen" in deficiencies:
            recommendations.append("Apply nitrogen-rich fertilizer in split doses.")
        if "phosphorus" in deficiencies:
            recommendations.append("Incorporate phosphorus fertilizer near root zone.")
        if "potassium" in deficiencies:
            recommendations.append("Apply potash fertilizer to improve crop resilience.")
        if "ph" in deficiencies:
            recommendations.append("Raise soil pH with agricultural lime.")
        if "ph" in excesses:
            recommendations.append("Lower soil pH with sulfur-based amendment.")

        if not recommendations:
            recommendations.append("Soil profile is balanced; maintain current nutrient program.")

        overall_health = "optimal" if not deficiencies and not excesses else "needs_attention"
        logger.info("Soil analysis complete: overall_health=%s", overall_health)
        return {
            "overall_health": overall_health,
            "nutrient_levels": nutrient_levels,
            "deficiencies": deficiencies,
            "recommendations": recommendations,
        }

    @staticmethod
    def _classify_range(value: float, low: float, high: float) -> str:
        if value < low:
            return "low"
        if value > high:
            return "high"
        return "optimal"
