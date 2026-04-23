from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, TypedDict


class AgriculturalState(TypedDict, total=False):
    user_id: str
    input_type: Literal["text", "image", "voice", "multimodal"]
    input_data: Any
    query: str
    language: Literal["ar", "en"]
    timestamp: str
    vision_result: dict[str, Any]
    voice_text: str
    vector_context: list[dict[str, Any]]
    graph_paths: list[dict[str, Any]]
    reasoning_depth: int
    enriched_context: str
    final_answer_en: str
    final_answer_ar: str
    confidence: float
    reasoning: str
    sources: list[str]
    error: str
    optional_audio: bytes


def initial_state(user_id: str = "anonymous", input_data: Any = "") -> AgriculturalState:
    return AgriculturalState(
        user_id=user_id,
        input_type="text",
        input_data=input_data,
        query="",
        language="ar",
        timestamp=datetime.now(timezone.utc).isoformat(),
        vision_result={"disease": "unknown", "confidence": 0.0, "symptoms": []},
        voice_text="",
        vector_context=[],
        graph_paths=[],
        reasoning_depth=0,
        enriched_context="",
        final_answer_en="",
        final_answer_ar="",
        confidence=0.0,
        reasoning="",
        sources=[],
        error="",
    )
