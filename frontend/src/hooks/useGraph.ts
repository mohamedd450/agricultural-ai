import { useState, useCallback } from "react";
import { DiagnosisResponse, GraphNode, GraphEdge } from "../services/api";

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface UseGraphReturn {
  graphData: GraphData;
  updateGraph: (diagnosisResponse: DiagnosisResponse) => void;
  clearGraph: () => void;
}

const EMPTY_GRAPH: GraphData = { nodes: [], edges: [] };

/**
 * Parse a single graph_path string such as
 *   "Crop:Tomato -> CAUSES -> Disease:Blight"
 * into nodes and edges.
 */
function parsePath(
  path: string,
  existingNodeIds: Set<string>
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  const segments = path.split("->").map((s) => s.trim());

  let lastNodeId: string | null = null;

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];

    // Node segments contain a colon  "Type:Label"
    if (segment.includes(":")) {
      const colonIdx = segment.indexOf(":");
      const type = segment.substring(0, colonIdx).trim();
      const label = segment.substring(colonIdx + 1).trim();
      const id = `${type}:${label}`;

      if (!existingNodeIds.has(id)) {
        existingNodeIds.add(id);
        nodes.push({ id, label, type, properties: {} });
      }

      // If we have a pending relationship from the previous segment, create edge
      if (lastNodeId !== null && i >= 2) {
        const relationship = segments[i - 1].trim();
        edges.push({
          source: lastNodeId,
          target: id,
          relationship,
          weight: 1.0,
        });
      }

      lastNodeId = id;
    }
    // Odd-indexed segments are relationship labels – handled above
  }

  return { nodes, edges };
}

export default function useGraph(): UseGraphReturn {
  const [graphData, setGraphData] = useState<GraphData>(EMPTY_GRAPH);

  const updateGraph = useCallback(
    (diagnosisResponse: DiagnosisResponse) => {
      const allNodes: GraphNode[] = [];
      const allEdges: GraphEdge[] = [];
      const nodeIds = new Set<string>();

      for (const path of diagnosisResponse.graph_paths) {
        const { nodes, edges } = parsePath(path, nodeIds);
        allNodes.push(...nodes);
        allEdges.push(...edges);
      }

      setGraphData({ nodes: allNodes, edges: allEdges });
    },
    []
  );

  const clearGraph = useCallback(() => {
    setGraphData(EMPTY_GRAPH);
  }, []);

  return { graphData, updateGraph, clearGraph };
}
