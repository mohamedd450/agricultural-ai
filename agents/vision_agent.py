from __future__ import annotations

from langgraph_core.state import AgriculturalState


_DEFAULT = {"disease": "unknown", "confidence": 0.0, "symptoms": []}


def run(state: AgriculturalState) -> AgriculturalState:
    payload = state.get("input_data")
    image_hint = ""
    if isinstance(payload, dict):
        image_hint = str(payload.get("image", "")).lower()
    elif isinstance(payload, str):
        image_hint = payload.lower()

    result = dict(_DEFAULT)
    if any(token in image_hint for token in ("yellow", "صفر")):
        result = {
            "disease": "nitrogen_deficiency",
            "confidence": 0.91,
            "symptoms": ["yellow_leaves", "chlorosis"],
        }

    return {**state, "vision_result": result}
