"""Unit tests for new agronomy-oriented core services."""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx
import pytest

from app.services.crop_health_service import CropHealthService
from app.services.soil_analysis_service import SoilAnalysisService
from app.services.weather_service import WeatherService
from app.utils.exceptions import InvalidInputError, ServiceUnavailableError


@pytest.mark.asyncio
async def test_crop_health_predicts_critical_status() -> None:
    service = CropHealthService()
    result = await service.predict_health(
        {
            "soil_moisture": 18,
            "temperature_c": 38,
            "humidity": 75,
            "rainfall_mm_7d": 0,
            "leaf_discoloration": 0.9,
            "pest_activity": 0.8,
        }
    )
    assert result["health_status"] == "critical"
    assert result["risk_score"] > 0.75
    assert result["recommendations"]


@pytest.mark.asyncio
async def test_soil_analysis_detects_deficiencies() -> None:
    service = SoilAnalysisService()
    result = await service.analyze(
        {
            "nitrogen": 10,
            "phosphorus": 10,
            "potassium": 100,
            "ph": 5.2,
            "moisture": 40,
        }
    )
    assert result["overall_health"] == "needs_attention"
    assert "nitrogen" in result["deficiencies"]
    assert "phosphorus" in result["deficiencies"]
    assert "ph" in result["deficiencies"]


@pytest.mark.asyncio
async def test_weather_recommendation_increase_irrigation() -> None:
    service = WeatherService()
    result = await service.generate_recommendations(
        weather={
            "temperature_c": 35,
            "humidity": 35,
            "wind_speed_kmh": 8,
            "precipitation_mm": 0,
        },
        crop_type="tomato",
    )
    assert result["irrigation_alert"] == "increase"
    assert any("Increase irrigation" in item for item in result["recommendations"])


@pytest.mark.asyncio
async def test_weather_service_raises_on_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    service = WeatherService()

    class _FailingClient:
        async def __aenter__(self) -> "_FailingClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            return None

        async def get(self, *args: Any, **kwargs: Any) -> None:
            raise httpx.ConnectError("network down")

    monkeypatch.setattr("app.services.weather_service.httpx.AsyncClient", lambda *args, **kwargs: _FailingClient())

    with pytest.raises(ServiceUnavailableError):
        await service.get_current_weather(latitude=30.0, longitude=31.0)


@pytest.mark.asyncio
async def test_crop_health_rejects_missing_features() -> None:
    service = CropHealthService()
    with pytest.raises(InvalidInputError):
        await service.predict_health({"soil_moisture": 10})


@pytest.mark.asyncio
async def test_weather_service_raises_on_incomplete_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    service = WeatherService()

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"current": {"temperature_2m": 20.0}}

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            return None

        async def get(self, *args: Any, **kwargs: Any) -> _Response:
            return _Response()

    monkeypatch.setattr("app.services.weather_service.httpx.AsyncClient", lambda *args, **kwargs: _Client())
    with pytest.raises(ServiceUnavailableError):
        await service.get_current_weather(latitude=30.0, longitude=31.0)
