import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { AnalysisHistoryItem } from "../services/api";

interface HistoryPanelProps {
  items: AnalysisHistoryItem[];
  isLoading: boolean;
}

const PAGE_SIZE = 10;

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    maxWidth: 800,
    margin: "0 auto",
    fontFamily: "system-ui, sans-serif",
  },
  title: {
    fontSize: 20,
    fontWeight: 700,
    color: "#0f172a",
    marginBottom: 16,
  },
  table: {
    width: "100%",
    borderCollapse: "collapse" as const,
    background: "#fff",
    borderRadius: 12,
    overflow: "hidden",
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  },
  th: {
    padding: "12px 16px",
    textAlign: "start" as const,
    fontSize: 12,
    fontWeight: 700,
    textTransform: "uppercase" as const,
    color: "#64748b",
    background: "#f8fafc",
    borderBottom: "1px solid #e2e8f0",
    letterSpacing: 0.5,
  },
  td: {
    padding: "12px 16px",
    fontSize: 14,
    color: "#334155",
    borderBottom: "1px solid #f1f5f9",
    verticalAlign: "top" as const,
  },
  confidenceBadge: {
    display: "inline-block",
    padding: "2px 10px",
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 600,
  },
  emptyState: {
    textAlign: "center" as const,
    padding: 48,
    color: "#94a3b8",
    fontSize: 15,
  },
  pagination: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: 12,
    marginTop: 16,
  },
  pageBtn: {
    padding: "8px 18px",
    border: "1px solid #e2e8f0",
    borderRadius: 6,
    background: "#fff",
    color: "#334155",
    cursor: "pointer",
    fontSize: 14,
  },
  pageBtnDisabled: {
    opacity: 0.4,
    cursor: "not-allowed",
  },
  pageInfo: {
    fontSize: 13,
    color: "#64748b",
  },
  skeleton: {
    height: 14,
    borderRadius: 4,
    background: "#e2e8f0",
  },
};

function confidenceStyle(confidence: number): React.CSSProperties {
  const pct = Math.round(confidence * 100);
  let bg: string;
  let color: string;
  if (confidence >= 0.8) {
    bg = "#dcfce7";
    color = "#166534";
  } else if (confidence >= 0.5) {
    bg = "#fef9c3";
    color = "#854d0e";
  } else {
    bg = "#fee2e2";
    color = "#991b1b";
  }
  return { ...styles.confidenceBadge, backgroundColor: bg, color };
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({ items, isLoading }) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === "ar";
  const [page, setPage] = useState(0);

  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageItems = items.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  if (isLoading) {
    return (
      <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
        <div style={styles.title}>{t("history.title")}</div>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>{t("history.date")}</th>
              <th style={styles.th}>{t("history.query")}</th>
              <th style={styles.th}>{t("history.result")}</th>
              <th style={styles.th}>{t("analysis.confidence")}</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i}>
                <td style={styles.td}><div style={{ ...styles.skeleton, width: 100 }} /></td>
                <td style={styles.td}><div style={{ ...styles.skeleton, width: 160 }} /></td>
                <td style={styles.td}><div style={{ ...styles.skeleton, width: 120 }} /></td>
                <td style={styles.td}><div style={{ ...styles.skeleton, width: 60 }} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
        <div style={styles.title}>{t("history.title")}</div>
        <div style={styles.emptyState}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>📋</div>
          {t("history.noHistory")}
        </div>
      </div>
    );
  }

  return (
    <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
      <div style={styles.title}>{t("history.title")}</div>

      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>{t("history.date")}</th>
            <th style={styles.th}>{t("history.query")}</th>
            <th style={styles.th}>{t("history.result")}</th>
            <th style={styles.th}>{t("analysis.confidence")}</th>
          </tr>
        </thead>
        <tbody>
          {pageItems.map((item) => (
            <tr key={item.id}>
              <td style={styles.td}>{formatDate(item.timestamp)}</td>
              <td style={styles.td}>{item.query}</td>
              <td style={styles.td}>{item.diagnosis}</td>
              <td style={styles.td}>
                <span style={confidenceStyle(item.confidence)}>
                  {Math.round(item.confidence * 100)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div style={styles.pagination}>
          <button
            type="button"
            style={{
              ...styles.pageBtn,
              ...(page === 0 ? styles.pageBtnDisabled : {}),
            }}
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            {isRTL ? "→" : "←"} {isRTL ? "السابق" : "Prev"}
          </button>
          <span style={styles.pageInfo}>
            {page + 1} / {totalPages}
          </span>
          <button
            type="button"
            style={{
              ...styles.pageBtn,
              ...(page >= totalPages - 1 ? styles.pageBtnDisabled : {}),
            }}
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            {isRTL ? "التالي" : "Next"} {isRTL ? "←" : "→"}
          </button>
        </div>
      )}
    </div>
  );
};

export default HistoryPanel;
