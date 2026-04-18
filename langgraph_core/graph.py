from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from agents import decision_agent, edgequake_agent, fusion_agent, router_agent, vision_agent, voice_agent
from langgraph_core.state import AgriculturalState, initial_state

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    END = None
    StateGraph = None


async def _vision_node(state: AgriculturalState) -> AgriculturalState:
    return vision_agent.run(state)


async def _voice_node(state: AgriculturalState) -> AgriculturalState:
    return await voice_agent.run(state)


async def _multimodal_node(state: AgriculturalState) -> AgriculturalState:
    vision_task = asyncio.create_task(_vision_node(state))
    voice_task = asyncio.create_task(_voice_node(state))
    vision_state, voice_state = await asyncio.gather(vision_task, voice_task)
    merged = dict(state)
    merged.update(
        {
            "vision_result": vision_state.get("vision_result"),
            "voice_text": voice_state.get("voice_text", ""),
        }
    )
    if voice_state.get("query"):
        merged["query"] = voice_state["query"]
    return merged


async def _router_node(state: AgriculturalState) -> AgriculturalState:
    return router_agent.run(state)


async def _edgequake_node(state: AgriculturalState) -> AgriculturalState:
    return edgequake_agent.run(state)


async def _fusion_node(state: AgriculturalState) -> AgriculturalState:
    return fusion_agent.run(state)


async def _decision_node(state: AgriculturalState) -> AgriculturalState:
    return decision_agent.run(state)


def _route_from_input_type(state: AgriculturalState) -> str:
    return {
        "image": "vision_agent",
        "voice": "voice_agent",
        "multimodal": "multimodal_agent",
    }.get(state.get("input_type", "text"), "edgequake_agent")


def build_graph() -> Callable[[AgriculturalState], Awaitable[AgriculturalState]]:
    if StateGraph is None:
        async def fallback(state: AgriculturalState) -> AgriculturalState:
            state = await _router_node(state)
            route = _route_from_input_type(state)
            if route == "vision_agent":
                state = await _vision_node(state)
            elif route == "voice_agent":
                state = await _voice_node(state)
            elif route == "multimodal_agent":
                state = await _multimodal_node(state)
            state = await _edgequake_node(state)
            state = await _fusion_node(state)
            return await _decision_node(state)

        return fallback

    graph = StateGraph(AgriculturalState)
    graph.add_node("router", _router_node)
    graph.add_node("vision_agent", _vision_node)
    graph.add_node("voice_agent", _voice_node)
    graph.add_node("multimodal_agent", _multimodal_node)
    graph.add_node("edgequake_agent", _edgequake_node)
    graph.add_node("fusion_agent", _fusion_node)
    graph.add_node("decision_agent", _decision_node)
    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        _route_from_input_type,
        {
            "vision_agent": "vision_agent",
            "voice_agent": "voice_agent",
            "multimodal_agent": "multimodal_agent",
            "edgequake_agent": "edgequake_agent",
        },
    )
    graph.add_edge("vision_agent", "edgequake_agent")
    graph.add_edge("voice_agent", "edgequake_agent")
    graph.add_edge("multimodal_agent", "edgequake_agent")
    graph.add_edge("edgequake_agent", "fusion_agent")
    graph.add_edge("fusion_agent", "decision_agent")
    graph.add_edge("decision_agent", END)
    workflow = graph.compile()

    async def invoke(state: AgriculturalState) -> AgriculturalState:
        return await workflow.ainvoke(state)

    return invoke


async def run_workflow(input_data: str | dict, user_id: str = "anonymous") -> AgriculturalState:
    state = initial_state(user_id=user_id, input_data=input_data)
    graph_runner = build_graph()
    return await graph_runner(state)
