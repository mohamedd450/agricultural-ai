import { useState, useCallback, useMemo } from 'react';
import Graph from 'graphology';
import { GraphPath } from '../services/api';

const NODE_COLORS: Record<string, string> = {
  Disease: '#e63946',
  Symptom: '#f4a261',
  Crop: '#2a9d8f',
  Treatment: '#457b9d',
};

interface UseGraphReturn {
  graph: Graph | null;
  buildGraph: (paths: GraphPath[]) => void;
  nodeColors: Record<string, string>;
  clear: () => void;
}

export const useGraph = (): UseGraphReturn => {
  const [graph, setGraph] = useState<Graph | null>(null);

  const buildGraph = useCallback((paths: GraphPath[]) => {
    const g = new Graph();

    paths.forEach((path) => {
      path.nodes.forEach((node) => {
        if (!g.hasNode(node.id)) {
          g.addNode(node.id, {
            label: node.label,
            size: 15,
            color: NODE_COLORS[node.type] || '#999',
            x: Math.random() * 100,
            y: Math.random() * 100,
            nodeType: node.type,
          });
        }
      });

      path.edges.forEach((edge) => {
        const edgeKey = `${edge.source}-${edge.target}`;
        if (!g.hasEdge(edgeKey) && g.hasNode(edge.source) && g.hasNode(edge.target)) {
          g.addEdgeWithKey(edgeKey, edge.source, edge.target, {
            label: edge.label,
            size: 2,
          });
        }
      });
    });

    setGraph(g);
  }, []);

  const clear = useCallback(() => setGraph(null), []);

  const nodeColors = useMemo(() => NODE_COLORS, []);

  return { graph, buildGraph, nodeColors, clear };
};
