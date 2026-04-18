from __future__ import annotations

from langgraph_core.state import AgriculturalState
from knowledge_base.treatment_db import TREATMENT_DB


def run(state: AgriculturalState) -> AgriculturalState:
    disease = state.get("vision_result", {}).get("disease", "nitrogen_deficiency")
    if disease not in TREATMENT_DB:
        disease = "nitrogen_deficiency"

    treatment = TREATMENT_DB[disease]
    confidence = max(
        float(state.get("vision_result", {}).get("confidence", 0.0)),
        max((float(path.get("confidence", 0.0)) for path in state.get("graph_paths", [])), default=0.0),
    )

    answer_en = (
        f"Your plant shows {disease.replace('_', ' ')} symptoms with {confidence:.0%} confidence. "
        f"{treatment['answer_en']}"
    )
    answer_ar = (
        f"النبات يعاني من {disease.replace('_', ' ')} بدرجة ثقة {confidence:.0%}. "
        f"{treatment['answer_ar']}"
    )

    return {
        **state,
        "final_answer_en": answer_en,
        "final_answer_ar": answer_ar,
        "confidence": round(confidence, 2),
        "reasoning": state.get("enriched_context", ""),
        "sources": treatment["sources"],
        "optional_audio": answer_ar.encode("utf-8"),
    }
