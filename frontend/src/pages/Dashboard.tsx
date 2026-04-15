import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const stats = [
    { label: t("nav.analysis"), value: "—", color: "#2d6a4f" },
    { label: t("analysis.diagnosis"), value: "—", color: "#40916c" },
    { label: t("analysis.confidence"), value: "—", color: "#52b788" },
  ];

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ marginTop: 0, color: "#2d6a4f" }}>{t("app.title")}</h2>
        <p style={{ color: "#666", fontSize: 16 }}>{t("app.subtitle")}</p>
      </div>

      {/* Stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 20,
          marginBottom: 32,
        }}
      >
        {stats.map((card) => (
          <div
            key={card.label}
            style={{
              backgroundColor: "#fff",
              borderRadius: 12,
              padding: 24,
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
              borderTop: `4px solid ${card.color}`,
            }}
          >
            <p style={{ margin: 0, fontSize: 14, color: "#666" }}>{card.label}</p>
            <p style={{ margin: "8px 0 0", fontSize: 32, fontWeight: 700, color: card.color }}>
              {card.value}
            </p>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <h3 style={{ color: "#2d6a4f" }}>
        {t("nav.analysis")}
      </h3>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <button
          onClick={() => navigate("/analysis")}
          style={{
            padding: "16px 32px",
            backgroundColor: "#2d6a4f",
            color: "#fff",
            border: "none",
            borderRadius: 12,
            fontSize: 16,
            cursor: "pointer",
          }}
        >
          📸 {t("analysis.uploadImage")}
        </button>
        <button
          onClick={() => navigate("/analysis")}
          style={{
            padding: "16px 32px",
            backgroundColor: "#40916c",
            color: "#fff",
            border: "none",
            borderRadius: 12,
            fontSize: 16,
            cursor: "pointer",
          }}
        >
          🎤 {t("voice.record")}
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
