from __future__ import annotations

from langgraph_core.state import AgriculturalState


def run(state: AgriculturalState) -> AgriculturalState:
    query = state.get("query", "")
    disease = state.get("vision_result", {}).get("disease", "unknown")
    context_bits = [
        f"query={query}",
        f"disease={disease}",
        f"vector_matches={len(state.get('vector_context', []))}",
        f"graph_paths={len(state.get('graph_paths', []))}",
    ]
    return {**state, "enriched_context": " | ".join(context_bits)}
