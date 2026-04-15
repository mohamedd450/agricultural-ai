import React from "react";
import { useTranslation } from "react-i18next";

const History: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h2 style={{ marginTop: 0, color: "#2d6a4f" }}>
        {t("history.title")}
      </h2>

      <div
        style={{
          backgroundColor: "#fff",
          borderRadius: 12,
          padding: 24,
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr
              style={{
                borderBottom: "2px solid #e0e0e0",
                textAlign: "start",
              }}
            >
              <th style={{ padding: "12px 8px", color: "#2d6a4f" }}>
                {t("history.date")}
              </th>
              <th style={{ padding: "12px 8px", color: "#2d6a4f" }}>
                {t("history.query")}
              </th>
              <th style={{ padding: "12px 8px", color: "#2d6a4f" }}>
                {t("history.result")}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td
                colSpan={3}
                style={{
                  padding: 32,
                  textAlign: "center",
                  color: "#888",
                }}
              >
                {t("history.noHistory")}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default History;
