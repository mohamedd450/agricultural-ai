"""Shared pytest fixtures for the Agricultural AI platform test suite.

Provides mock service instances, sample data, and a FastAPI TestClient.
"""

from __future__ import annotations

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Mock service factories ────────────────────────────────────────────────


@pytest.fixture()
def mock_vision_service():
    """Return a mock VisionService with pre-set responses."""
    svc = MagicMock()
    svc.is_loaded = True
    svc.analyze_image = AsyncMock(
        return_value={
            "class": "nitrogen_deficiency",
            "confidence": 0.91,
            "all_predictions": [
                {"class": "nitrogen_deficiency", "confidence": 0.91},
                {"class": "iron_deficiency", "confidence": 0.06},
            ],
        }
    )
    svc.generate_heatmap = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    svc.load_model = AsyncMock()
    return svc


@pytest.fixture()
def mock_voice_service():
    """Return a mock VoiceService with pre-set responses."""
    svc = MagicMock()
    svc.is_loaded = True
    svc.speech_to_text = AsyncMock(
        return_value={
            "text": "ما هي مشكلة نبتتي؟",
            "language": "ar",
            "confidence": 0.88,
        }
    )
    svc.text_to_speech = AsyncMock(return_value=b"RIFF" + b"\x00" * 44)
    svc.load_model = AsyncMock()
    return svc


@pytest.fixture()
def mock_graph_rag_service():
    """Return a mock GraphRAGService with pre-set responses."""
    svc = MagicMock()
    svc.is_available = True
    svc.query = AsyncMock(
        return_value={
            "answer": "نقص النيتروجين – يُنصح باستخدام اليوريا",
            "confidence": 0.82,
            "graph_paths": [
                "أوراق صفراء → نقص النيتروجين → اليوريا",
            ],
            "reasoning_steps": ["Detected yellow leaves", "Matched nitrogen deficiency"],
        }
    )
    svc.multi_hop_reasoning = AsyncMock(
        return_value={
            "answer": "نقص النيتروجين",
            "confidence": 0.80,
            "graph_paths": ["أوراق صفراء → نقص النيتروجين → اليوريا"],
            "reasoning_steps": [],
            "paths": [],
        }
    )
    svc.initialize = AsyncMock()
    svc.close = AsyncMock()
    return svc


@pytest.fixture()
def mock_vector_db_service():
    """Return a mock VectorDBService with pre-set responses."""
    svc = MagicMock()
    svc.is_initialized = True
    svc.search = AsyncMock(
        return_value={
            "results": [
                {
                    "text": "Nitrogen deficiency causes yellowing of leaves.",
                    "score": 0.87,
                    "metadata": {"source": "fao_guide.pdf"},
                }
            ],
            "confidence": 0.87,
        }
    )
    svc.initialize = AsyncMock()
    svc.close = AsyncMock()
    return svc


@pytest.fixture()
def mock_cache_service():
    """Return a mock CacheService that simulates cache misses by default."""
    svc = MagicMock()
    svc.get = AsyncMock(return_value=None)
    svc.set = AsyncMock(return_value=True)
    svc.delete = AsyncMock(return_value=True)
    svc.initialize = AsyncMock()
    return svc


@pytest.fixture()
def mock_fusion_service():
    """Return a mock FusionService with pre-set fused result."""
    svc = MagicMock()
    svc.fuse = AsyncMock(
        return_value={
            "diagnosis": "نقص النيتروجين",
            "treatment": "تطبيق سماد اليوريا 46%",
            "confidence": 0.87,
            "graph_paths": ["أوراق صفراء → نقص النيتروجين → اليوريا"],
            "explanation": "تم التشخيص من دمج 3 مصادر معرفية",
            "source": "combined",
            "language": "ar",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
    )
    return svc


@pytest.fixture()
def mock_llm_service():
    """Return a mock LLMService with pre-set completion responses."""
    svc = MagicMock()
    svc.is_available = True
    svc.complete = AsyncMock(
        return_value={
            "text": "نقص النيتروجين – يُنصح بإضافة اليوريا بجرعة 50 كغ/هكتار",
            "tokens_used": 120,
            "model": "gpt-4o-mini",
            "success": True,
        }
    )
    svc.build_diagnosis_prompt = AsyncMock(
        return_value="ما تشخيص هذه الحالة الزراعية؟"
    )
    svc.generate_treatment_recommendation = AsyncMock(
        return_value={
            "treatment": "اليوريا 50 كغ/هكتار",
            "prevention": "تحليل التربة دورياً",
            "success": True,
        }
    )
    svc.translate = AsyncMock(side_effect=lambda text, **kw: text)
    return svc


@pytest.fixture()
def mock_decision_router():
    """Return a real DecisionRouter instance (no mocking needed)."""
    from app.services.decision_router import DecisionRouter

    return DecisionRouter()


# ── Sample data ───────────────────────────────────────────────────────────


@pytest.fixture()
def sample_image_bytes() -> bytes:
    """Return minimal valid PNG bytes for upload tests."""
    # 1×1 red pixel PNG
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture()
def sample_audio_bytes() -> bytes:
    """Return minimal WAV header bytes for voice tests."""
    # 44-byte WAV header (empty audio)
    return b"RIFF" + b"\x00" * 36 + b"data" + b"\x00" * 4


@pytest.fixture()
def sample_text_query_ar() -> str:
    return "ما هي مشكلة النبتة ذات الأوراق الصفراء؟"


@pytest.fixture()
def sample_text_query_en() -> str:
    return "What is the problem with the plant with yellow leaves?"


@pytest.fixture()
def sample_vision_result() -> dict:
    return {
        "class": "nitrogen_deficiency",
        "confidence": 0.91,
        "all_predictions": [
            {"class": "nitrogen_deficiency", "confidence": 0.91},
        ],
    }


@pytest.fixture()
def sample_graph_rag_result() -> dict:
    return {
        "answer": "نقص النيتروجين",
        "confidence": 0.82,
        "graph_paths": ["أوراق صفراء → نقص النيتروجين → اليوريا"],
        "reasoning_steps": [],
    }


@pytest.fixture()
def sample_vector_result() -> dict:
    return {
        "results": [
            {"text": "Nitrogen deficiency causes yellowing.", "score": 0.85}
        ],
        "confidence": 0.85,
    }


@pytest.fixture()
def sample_routing_decision() -> dict:
    return {
        "strategy": "vision_primary",
        "primary_source": "vision",
        "confidence": 0.91,
        "reasoning": "High vision confidence",
    }


# ── FastAPI TestClient ────────────────────────────────────────────────────


@pytest.fixture()
def test_client():
    """Return a synchronous FastAPI TestClient for endpoint testing."""
    from app.main import app

    with TestClient(app) as client:
        yield client
