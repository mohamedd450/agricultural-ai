import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import Graph from "graphology";
import { SigmaContainer } from "@sigmajs/react";
import { GraphNode, GraphEdge } from "../services/api";

interface GraphVisualizationProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const NODE_COLORS: Record<string, string> = {
  disease: "#ef4444",
  symptom: "#eab308",
  treatment: "#22c55e",
  crop: "#3b82f6",
  fertilizer: "#f97316",
};

const DEFAULT_NODE_COLOR = "#94a3b8";

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    height: 480,
    border: "1px solid #e2e8f0",
    borderRadius: 12,
    overflow: "hidden",
    background: "#fff",
    position: "relative",
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    color: "#94a3b8",
    fontSize: 15,
    gap: 8,
  },
  legend: {
    position: "absolute",
    bottom: 12,
    left: 12,
    display: "flex",
    flexWrap: "wrap",
    gap: 10,
    padding: "6px 10px",
    background: "rgba(255,255,255,0.9)",
    borderRadius: 8,
    fontSize: 12,
    zIndex: 10,
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: 4,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    flexShrink: 0,
  },
};

function buildGraph(nodes: GraphNode[], edges: GraphEdge[]): Graph {
  const graph = new Graph({ multi: true, type: "directed" });

  // Arrange nodes in a circle
  const count = nodes.length || 1;
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / count;
    const color = NODE_COLORS[node.type.toLowerCase()] ?? DEFAULT_NODE_COLOR;
    graph.addNode(node.id, {
      label: node.label,
      x: Math.cos(angle) * 100,
      y: Math.sin(angle) * 100,
      size: 12,
      color,
    });
  });

  edges.forEach((edge, i) => {
    if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
      graph.addEdgeWithKey(`e${i}`, edge.source, edge.target, {
        label: edge.relationship,
        size: Math.max(1, edge.weight * 2),
        color: "#cbd5e1",
        type: "arrow",
      });
    }
  });

  return graph;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({ nodes, edges }) => {
  const { t } = useTranslation();

  const graph = useMemo(() => buildGraph(nodes, edges), [nodes, edges]);

  if (nodes.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>
          <div style={{ fontSize: 36 }}>🕸️</div>
          <div>{t("analysis.noResults")}</div>
        </div>
      </div>
    );
  }

  const sigmaSettings = {
    renderLabels: true,
    renderEdgeLabels: true,
    defaultEdgeType: "arrow",
    labelSize: 14,
    labelColor: { color: "#1e293b" },
  };

  return (
    <div style={styles.container}>
      <SigmaContainer graph={graph} settings={sigmaSettings} style={{ width: "100%", height: "100%" }} />

      {/* Legend */}
      <div style={styles.legend}>
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} style={styles.legendItem}>
            <span style={{ ...styles.legendDot, backgroundColor: color }} />
            <span>{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GraphVisualization;
