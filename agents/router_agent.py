from __future__ import annotations

from langgraph_core.state import AgriculturalState
from utils.arabic_utils import detect_language


def run(state: AgriculturalState) -> AgriculturalState:
    payload = state.get("input_data")
    has_image = bool(state.get("image_data") or (isinstance(payload, dict) and payload.get("image")))
    has_voice = bool(state.get("audio_data") or (isinstance(payload, dict) and payload.get("audio")))

    if has_image and has_voice:
        input_type = "multimodal"
    elif has_image:
        input_type = "image"
    elif has_voice:
        input_type = "voice"
    else:
        input_type = "text"

    query = state.get("query") or (payload if isinstance(payload, str) else "")
    return {
        **state,
        "input_type": input_type,
        "query": query,
        "language": state.get("language") or detect_language(query),
    }
