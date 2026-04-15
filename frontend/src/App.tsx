import React, { useEffect } from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Dashboard from "./pages/Dashboard";
import Analysis from "./pages/Analysis";
import History from "./pages/History";
import Settings from "./pages/Settings";

const LanguageToggle: React.FC = () => {
  const { i18n } = useTranslation();
  const isArabic = i18n.language === "ar";

  const toggle = () => {
    i18n.changeLanguage(isArabic ? "en" : "ar");
  };

  return (
    <button
      onClick={toggle}
      style={{
        background: "none",
        border: "1px solid #ccc",
        borderRadius: 6,
        padding: "6px 14px",
        cursor: "pointer",
        fontSize: 14,
        color: "inherit",
      }}
    >
      {isArabic ? "EN" : "عربي"}
    </button>
  );
};

const App: React.FC = () => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === "ar";

  useEffect(() => {
    document.documentElement.dir = isRTL ? "rtl" : "ltr";
    document.documentElement.lang = i18n.language;
  }, [isRTL, i18n.language]);

  const navLinkStyle = ({ isActive }: { isActive: boolean }) => ({
    display: "block",
    padding: "12px 20px",
    textDecoration: "none",
    color: isActive ? "#fff" : "#c8e6c9",
    backgroundColor: isActive ? "rgba(255,255,255,0.15)" : "transparent",
    borderRadius: 8,
    marginBottom: 4,
    transition: "background-color 0.2s",
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: isRTL ? "row-reverse" : "row",
        minHeight: "100vh",
        fontFamily: isRTL
          ? "'Segoe UI', Tahoma, Arial, sans-serif"
          : "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      }}
    >
      {/* Sidebar */}
      <nav
        style={{
          width: 240,
          backgroundColor: "#2d6a4f",
          color: "#fff",
          padding: "24px 12px",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}
      >
        <div style={{ marginBottom: 32, textAlign: "center" }}>
          <h1 style={{ fontSize: 18, margin: 0 }}>{t("app.title")}</h1>
          <p style={{ fontSize: 12, margin: "8px 0 0", opacity: 0.8 }}>
            {t("app.subtitle")}
          </p>
        </div>

        <NavLink to="/" style={navLinkStyle} end>
          {t("nav.dashboard")}
        </NavLink>
        <NavLink to="/analysis" style={navLinkStyle}>
          {t("nav.analysis")}
        </NavLink>
        <NavLink to="/history" style={navLinkStyle}>
          {t("nav.history")}
        </NavLink>
        <NavLink to="/settings" style={navLinkStyle}>
          {t("nav.settings")}
        </NavLink>

        <div style={{ marginTop: "auto", textAlign: "center" }}>
          <LanguageToggle />
        </div>
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, padding: 32, backgroundColor: "#f5f5f5" }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
};

export default App;
