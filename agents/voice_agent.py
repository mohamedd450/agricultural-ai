from __future__ import annotations

from langgraph_core.state import AgriculturalState


async def speech_to_text(audio_data: bytes | str, language: str = "ar") -> str:
    if isinstance(audio_data, str):
        return audio_data
    try:
        return audio_data.decode("utf-8")
    except Exception:
        return ""


def text_to_speech(text: str, language: str = "ar") -> bytes:
    if not text:
        return b""
    return f"{language}:{text}".encode("utf-8")


async def run(state: AgriculturalState) -> AgriculturalState:
    payload = state.get("input_data")
    audio_data = payload.get("audio") if isinstance(payload, dict) else payload
    if not audio_data:
        return {**state, "voice_text": ""}
    voice_text = await speech_to_text(audio_data, language=state.get("language", "ar"))
    return {**state, "voice_text": voice_text, "query": state.get("query") or voice_text}
