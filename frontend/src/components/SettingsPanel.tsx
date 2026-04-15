import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { checkHealth, HealthStatus } from "../services/api";
import authService from "../services/auth";

const THEME_KEY = "app_theme";

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: "100%",
    maxWidth: 520,
    margin: "0 auto",
    fontFamily: "system-ui, sans-serif",
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: 700,
    color: "#0f172a",
  },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: 20,
    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    border: "1px solid #e2e8f0",
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 700,
    color: "#334155",
    marginBottom: 12,
  },
  row: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  label: {
    fontSize: 14,
    color: "#475569",
  },
  select: {
    padding: "8px 14px",
    borderRadius: 6,
    border: "1px solid #e2e8f0",
    fontSize: 14,
    color: "#334155",
    background: "#f8fafc",
    cursor: "pointer",
    outline: "none",
  },
  toggleGroup: {
    display: "flex",
    borderRadius: 8,
    overflow: "hidden",
    border: "1px solid #e2e8f0",
  },
  toggleBtn: {
    padding: "8px 20px",
    border: "none",
    fontSize: 14,
    cursor: "pointer",
    transition: "background 0.15s, color 0.15s",
  },
  toggleActive: {
    background: "#3b82f6",
    color: "#fff",
    fontWeight: 600,
  },
  toggleInactive: {
    background: "#f8fafc",
    color: "#64748b",
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    flexShrink: 0,
  },
  statusText: {
    fontSize: 14,
    color: "#475569",
  },
  userInfo: {
    fontSize: 14,
    color: "#334155",
    lineHeight: 1.8,
  },
  notAuth: {
    fontSize: 14,
    color: "#94a3b8",
    fontStyle: "italic" as const,
  },
};

const SettingsPanel: React.FC = () => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === "ar";

  const [theme, setTheme] = useState<"light" | "dark">(() => {
    return (localStorage.getItem(THEME_KEY) as "light" | "dark") || "light";
  });

  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState(false);

  // Apply theme to document
  useEffect(() => {
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  // Check API health
  useEffect(() => {
    let mounted = true;
    checkHealth()
      .then((status) => {
        if (mounted) {
          setHealthStatus(status);
          setHealthError(false);
        }
      })
      .catch(() => {
        if (mounted) setHealthError(true);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleLanguageChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const lng = e.target.value;
      i18n.changeLanguage(lng);
      document.documentElement.dir = lng === "ar" ? "rtl" : "ltr";
      document.documentElement.lang = lng;
    },
    [i18n]
  );

  const user = authService.getUser();

  const isConnected = healthStatus?.status === "healthy";

  return (
    <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
      <div style={styles.title}>{t("settings.title")}</div>

      {/* Language */}
      <div style={styles.card}>
        <div style={styles.cardTitle}>{t("settings.language")}</div>
        <div style={styles.row}>
          <span style={styles.label}>🌐 {t("settings.language")}</span>
          <select
            value={i18n.language}
            onChange={handleLanguageChange}
            style={styles.select}
          >
            <option value="ar">{t("settings.arabic")}</option>
            <option value="en">{t("settings.english")}</option>
          </select>
        </div>
      </div>

      {/* Theme */}
      <div style={styles.card}>
        <div style={styles.cardTitle}>{t("settings.theme")}</div>
        <div style={styles.row}>
          <span style={styles.label}>🎨 {t("settings.theme")}</span>
          <div style={styles.toggleGroup}>
            <button
              type="button"
              style={{
                ...styles.toggleBtn,
                ...(theme === "light" ? styles.toggleActive : styles.toggleInactive),
              }}
              onClick={() => setTheme("light")}
            >
              ☀️ {t("settings.light")}
            </button>
            <button
              type="button"
              style={{
                ...styles.toggleBtn,
                ...(theme === "dark" ? styles.toggleActive : styles.toggleInactive),
              }}
              onClick={() => setTheme("dark")}
            >
              🌙 {t("settings.dark")}
            </button>
          </div>
        </div>
      </div>

      {/* API Status */}
      <div style={styles.card}>
        <div style={styles.cardTitle}>API</div>
        <div style={styles.row}>
          <span
            style={{
              ...styles.statusDot,
              backgroundColor: healthError
                ? "#ef4444"
                : isConnected
                  ? "#22c55e"
                  : "#eab308",
            }}
          />
          <span style={styles.statusText}>
            {healthError
              ? "Disconnected"
              : isConnected
                ? `Connected — ${healthStatus?.status}`
                : t("common.loading")}
          </span>
        </div>
      </div>

      {/* User Info */}
      <div style={styles.card}>
        <div style={styles.cardTitle}>👤 User</div>
        {user ? (
          <div style={styles.userInfo}>
            <div>
              <strong>ID:</strong> {user.sub}
            </div>
          </div>
        ) : (
          <div style={styles.notAuth}>Not authenticated</div>
        )}
      </div>
    </div>
  );
};

export default SettingsPanel;
