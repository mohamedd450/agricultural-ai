import React from "react";
import { useTranslation } from "react-i18next";

const Settings: React.FC = () => {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div>
      <h2 style={{ marginTop: 0, color: "#2d6a4f" }}>
        {t("settings.title")}
      </h2>

      <div
        style={{
          backgroundColor: "#fff",
          borderRadius: 12,
          padding: 24,
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          maxWidth: 480,
        }}
      >
        {/* Language setting */}
        <div style={{ marginBottom: 24 }}>
          <label
            style={{
              display: "block",
              fontWeight: 600,
              marginBottom: 8,
              color: "#2d6a4f",
            }}
          >
            {t("settings.language")}
          </label>
          <div style={{ display: "flex", gap: 12 }}>
            <button
              onClick={() => changeLanguage("ar")}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "1px solid #2d6a4f",
                backgroundColor:
                  i18n.language === "ar" ? "#2d6a4f" : "transparent",
                color: i18n.language === "ar" ? "#fff" : "#2d6a4f",
                cursor: "pointer",
                fontSize: 14,
              }}
            >
              {t("settings.arabic")}
            </button>
            <button
              onClick={() => changeLanguage("en")}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "1px solid #2d6a4f",
                backgroundColor:
                  i18n.language === "en" ? "#2d6a4f" : "transparent",
                color: i18n.language === "en" ? "#fff" : "#2d6a4f",
                cursor: "pointer",
                fontSize: 14,
              }}
            >
              {t("settings.english")}
            </button>
          </div>
        </div>

        {/* Theme setting */}
        <div>
          <label
            style={{
              display: "block",
              fontWeight: 600,
              marginBottom: 8,
              color: "#2d6a4f",
            }}
          >
            {t("settings.theme")}
          </label>
          <div style={{ display: "flex", gap: 12 }}>
            <button
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "1px solid #2d6a4f",
                backgroundColor: "#2d6a4f",
                color: "#fff",
                cursor: "pointer",
                fontSize: 14,
              }}
            >
              {t("settings.light")}
            </button>
            <button
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "1px solid #2d6a4f",
                backgroundColor: "transparent",
                color: "#2d6a4f",
                cursor: "pointer",
                fontSize: 14,
              }}
            >
              {t("settings.dark")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
