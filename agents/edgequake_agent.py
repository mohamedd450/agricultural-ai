from __future__ import annotations

from langgraph_core.config import settings
from langgraph_core.state import AgriculturalState
from knowledge_base.disease_graph import get_paths_from_symptom
from utils.chroma_setup import build_default_store


_STORE = build_default_store()


def run(state: AgriculturalState) -> AgriculturalState:
    query = (state.get("query") or "").strip()
    symptom_id = "yellow_leaves" if ("yellow" in query.lower() or "صفر" in query) else "yellow_leaves"
    vector_context = _STORE.search("nitrogen", top_k=3)
    graph_paths = get_paths_from_symptom(symptom_id, max_depth=min(settings.max_reasoning_depth, 3))
    return {
        **state,
        "vector_context": vector_context,
        "graph_paths": graph_paths,
        "reasoning_depth": min(settings.max_reasoning_depth, 3),
    }
