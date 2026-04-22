"""Weather integration service for weather-aware agronomy recommendations."""

from __future__ import annotations

import httpx

from app.config import get_settings
from app.utils.exceptions import ServiceUnavailableError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherService:
    """Fetch weather data and transform it into actionable recommendations."""

    async def get_current_weather(self, latitude: float, longitude: float) -> dict:
        """Fetch current weather details from the configured weather API."""
        settings = get_settings()
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.weather_timeout_seconds) as client:
                response = await client.get(settings.weather_api_url, params=params)
                response.raise_for_status()
                payload = response.json()
            current = payload.get("current", {})
            required_fields = {
                "temperature_2m",
                "relative_humidity_2m",
                "wind_speed_10m",
                "precipitation",
            }
            missing_fields = sorted(field for field in required_fields if field not in current)
            if missing_fields:
                raise ServiceUnavailableError(
                    message="Weather provider returned incomplete data.",
                    error_code="WEATHER_PROVIDER_INVALID_RESPONSE",
                    details={"missing_fields": missing_fields},
                )
            return {
                "temperature_c": float(current["temperature_2m"]),
                "humidity": float(current["relative_humidity_2m"]),
                "wind_speed_kmh": float(current["wind_speed_10m"]),
                "precipitation_mm": float(current["precipitation"]),
            }
        except ServiceUnavailableError:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.error("Weather lookup failed", exc_info=True)
            raise ServiceUnavailableError(
                message="Unable to fetch weather data at this time.",
                error_code="WEATHER_PROVIDER_UNAVAILABLE",
                details={"error": str(exc)},
            ) from exc

    async def generate_recommendations(
        self,
        weather: dict[str, float],
        crop_type: str | None = None,
    ) -> dict:
        """Build weather-driven field recommendations from current conditions."""
        recommendations: list[str] = []
        irrigation_alert = "normal"

        if weather["precipitation_mm"] > 5:
            irrigation_alert = "reduce"
            recommendations.append("Reduce irrigation due to ongoing rainfall.")
        elif weather["temperature_c"] > 32 and weather["humidity"] < 50:
            irrigation_alert = "increase"
            recommendations.append("Increase irrigation to prevent heat stress.")

        if weather["wind_speed_kmh"] > 25:
            recommendations.append("Avoid foliar spray application during high wind.")

        if crop_type:
            recommendations.append(f"Prioritize {crop_type} scouting based on current weather shifts.")

        if not recommendations:
            recommendations.append("Weather conditions are stable; continue standard operations.")

        return {
            "current_weather": weather,
            "recommendations": recommendations,
            "irrigation_alert": irrigation_alert,
        }
