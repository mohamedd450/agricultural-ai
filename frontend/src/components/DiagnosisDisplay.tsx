import React from "react";
import { useTranslation } from "react-i18next";
import { DiagnosisResponse } from "../services/api";

interface DiagnosisDisplayProps {
  diagnosis: DiagnosisResponse | null;
  isLoading: boolean;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "#22c55e";
  if (confidence >= 0.5) return "#eab308";
  return "#ef4444";
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    maxWidth: 600,
    margin: "0 auto",
    fontFamily: "system-ui, sans-serif",
  },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: 24,
    boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
    border: "1px solid #e2e8f0",
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: 700,
    textTransform: "uppercase" as const,
    color: "#64748b",
    marginBottom: 6,
    letterSpacing: 0.5,
  },
  sectionValue: {
    fontSize: 15,
    color: "#1e293b",
    lineHeight: 1.6,
  },
  diagnosisName: {
    fontSize: 22,
    fontWeight: 700,
    color: "#0f172a",
    marginBottom: 16,
  },
  confidenceBar: {
    width: "100%",
    height: 10,
    backgroundColor: "#e2e8f0",
    borderRadius: 5,
    overflow: "hidden",
    marginTop: 4,
  },
  confidenceFill: {
    height: "100%",
    borderRadius: 5,
    transition: "width 0.4s ease",
  },
  confidenceLabel: {
    fontSize: 14,
    fontWeight: 600,
    marginTop: 4,
  },
  pathItem: {
    fontSize: 13,
    color: "#475569",
    padding: "4px 8px",
    background: "#f1f5f9",
    borderRadius: 6,
    marginBottom: 4,
    fontFamily: "monospace",
    wordBreak: "break-all" as const,
  },
  emptyState: {
    textAlign: "center" as const,
    padding: 48,
    color: "#94a3b8",
    fontSize: 15,
  },
  skeleton: {
    background: "linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)",
    backgroundSize: "200% 100%",
    animation: "shimmer 1.5s infinite",
    borderRadius: 6,
    height: 16,
    marginBottom: 12,
  },
  skeletonWide: {
    width: "100%",
  },
  skeletonMed: {
    width: "70%",
  },
  skeletonShort: {
    width: "40%",
  },
  source: {
    fontSize: 12,
    color: "#94a3b8",
    fontStyle: "italic" as const,
    borderTop: "1px solid #e2e8f0",
    paddingTop: 12,
    marginTop: 8,
  },
};

const SkeletonBlock: React.FC<{ width?: string }> = ({ width = "100%" }) => (
  <div style={{ ...styles.skeleton, width }} />
);

const DiagnosisDisplay: React.FC<DiagnosisDisplayProps> = ({ diagnosis, isLoading }) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === "ar";

  if (isLoading) {
    return (
      <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
        <div style={styles.card}>
          <SkeletonBlock width="60%" />
          <SkeletonBlock width="100%" />
          <SkeletonBlock width="100%" />
          <SkeletonBlock width="80%" />
          <SkeletonBlock width="45%" />
          <SkeletonBlock width="100%" />
          <SkeletonBlock width="70%" />
        </div>
      </div>
    );
  }

  if (!diagnosis) {
    return (
      <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
        <div style={styles.emptyState}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🌱</div>
          {t("analysis.noResults")}
        </div>
      </div>
    );
  }

  const confidencePercent = Math.round(diagnosis.confidence * 100);
  const confidenceColor = getConfidenceColor(diagnosis.confidence);

  return (
    <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
      <div style={styles.card}>
        {/* Diagnosis Name */}
        <div style={styles.diagnosisName}>{diagnosis.diagnosis}</div>

        {/* Confidence */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>{t("analysis.confidence")}</div>
          <div style={styles.confidenceBar}>
            <div
              style={{
                ...styles.confidenceFill,
                width: `${confidencePercent}%`,
                backgroundColor: confidenceColor,
              }}
            />
          </div>
          <div style={{ ...styles.confidenceLabel, color: confidenceColor }}>
            {confidencePercent}%
          </div>
        </div>

        {/* Treatment */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>{t("analysis.treatment")}</div>
          <div style={styles.sectionValue}>{diagnosis.treatment}</div>
        </div>

        {/* Explanation */}
        {diagnosis.explanation && (
          <div style={styles.section}>
            <div style={styles.sectionTitle}>{t("analysis.explanation")}</div>
            <div style={styles.sectionValue}>{diagnosis.explanation}</div>
          </div>
        )}

        {/* Graph Paths */}
        {diagnosis.graph_paths.length > 0 && (
          <div style={styles.section}>
            <div style={styles.sectionTitle}>{t("analysis.graphPaths")}</div>
            {diagnosis.graph_paths.map((path, idx) => (
              <div key={idx} style={styles.pathItem}>
                {path}
              </div>
            ))}
          </div>
        )}

        {/* Source */}
        {diagnosis.source && (
          <div style={styles.source}>
            {t("analysis.source")}: {diagnosis.source}
          </div>
        )}
      </div>
    </div>
  );
};

export default DiagnosisDisplay;
