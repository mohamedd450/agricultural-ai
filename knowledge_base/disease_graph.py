from __future__ import annotations

import networkx as nx

DISEASE_GRAPH = {
    "nodes": [
        {"id": "yellow_leaves", "label": "أوراق صفراء", "type": "symptom"},
        {"id": "chlorophyll_breakdown", "label": "تحلل الكلوروفيل", "type": "process"},
        {"id": "nitrogen_deficiency", "label": "نقص النيتروجين", "type": "disease"},
        {"id": "urea_fertilizer", "label": "سماد اليوريا", "type": "treatment"},
    ],
    "edges": [
        {"from": "yellow_leaves", "to": "chlorophyll_breakdown", "weight": 0.9},
        {"from": "chlorophyll_breakdown", "to": "nitrogen_deficiency", "weight": 0.95},
        {"from": "nitrogen_deficiency", "to": "urea_fertilizer", "weight": 0.9},
    ],
}


def build_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    for node in DISEASE_GRAPH["nodes"]:
        graph.add_node(node["id"], **node)
    for edge in DISEASE_GRAPH["edges"]:
        graph.add_edge(edge["from"], edge["to"], weight=edge["weight"])
    return graph


def get_paths_from_symptom(symptom_id: str, max_depth: int = 3) -> list[dict]:
    graph = build_graph()
    paths: list[dict] = []
    for target in graph.nodes:
        if target == symptom_id:
            continue
        for path in nx.all_simple_paths(graph, symptom_id, target, cutoff=max_depth):
            labels = [graph.nodes[node].get("label", node) for node in path]
            conf = min(
                [graph[path[i]][path[i + 1]].get("weight", 0.0) for i in range(len(path) - 1)] or [0.0]
            )
            paths.append({"path": " → ".join(labels), "confidence": round(float(conf), 2)})
    return sorted(paths, key=lambda item: item["confidence"], reverse=True)
