import React from "react";
import { useTranslation } from "react-i18next";

const Dashboard: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h2 style={{ marginTop: 0, color: "#2d6a4f" }}>{t("nav.dashboard")}</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 20,
          marginTop: 24,
        }}
      >
        {[
          { label: t("nav.analysis"), value: "12", color: "#2d6a4f" },
          { label: t("analysis.diagnosis"), value: "8", color: "#40916c" },
          { label: t("analysis.confidence"), value: "94%", color: "#52b788" },
        ].map((card) => (
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
            <p style={{ margin: 0, fontSize: 14, color: "#666" }}>
              {card.label}
            </p>
            <p
              style={{
                margin: "8px 0 0",
                fontSize: 32,
                fontWeight: 700,
                color: card.color,
              }}
            >
              {card.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
