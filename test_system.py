from __future__ import annotations

import pytest

from langgraph_core.graph import run_workflow


@pytest.mark.asyncio
async def test_image_flow_detects_nitrogen_deficiency_from_yellow_leaf_hint() -> None:
    result = await run_workflow({"image": "yellow_leaf.jpg"}, user_id="u1")
    assert result["input_type"] == "image"
    assert result["vision_result"]["disease"] == "nitrogen_deficiency"
    assert result["confidence"] >= 0.9
    assert result["graph_paths"]
    assert result["final_answer_en"]
    assert result["final_answer_ar"]


@pytest.mark.asyncio
async def test_voice_flow_populates_query_from_transcript() -> None:
    result = await run_workflow({"audio": "أوراق صفراء في الطماطم"}, user_id="u2")
    assert result["input_type"] == "voice"
    assert "أوراق" in result["query"]
    assert result["reasoning_depth"] <= 3


@pytest.mark.asyncio
async def test_text_flow_keeps_reasoning_depth_cap() -> None:
    result = await run_workflow("yellow leaves on tomato", user_id="u3")
    assert result["input_type"] == "text"
    assert result["reasoning_depth"] <= 3
    assert isinstance(result["sources"], list)
