import React from 'react';
import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  Search,
  History,
  Settings,
  Globe,
  Leaf,
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import HistoryPage from './pages/History';
import SettingsPage from './pages/Settings';

const navItems = [
  { path: '/', icon: LayoutDashboard, labelKey: 'nav.dashboard' },
  { path: '/analysis', icon: Search, labelKey: 'nav.analysis' },
  { path: '/history', icon: History, labelKey: 'nav.history' },
  { path: '/settings', icon: Settings, labelKey: 'nav.settings' },
];

const App: React.FC = () => {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const isRTL = i18n.language === 'ar';

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ar' ? 'en' : 'ar';
    i18n.changeLanguage(newLang);
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = newLang;
  };

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    minHeight: '100vh',
    direction: isRTL ? 'rtl' : 'ltr',
    fontFamily: isRTL
      ? "'Segoe UI', Tahoma, Arial, sans-serif"
      : "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  };

  const sidebarStyle: React.CSSProperties = {
    width: 240,
    background: 'linear-gradient(180deg, #1b4332 0%, #2d6a4f 100%)',
    color: 'white',
    display: 'flex',
    flexDirection: 'column',
    padding: '20px 0',
    flexShrink: 0,
  };

  const mainStyle: React.CSSProperties = {
    flex: 1,
    background: '#f8f9fa',
    overflow: 'auto',
  };

  const headerStyle: React.CSSProperties = {
    background: 'white',
    padding: '16px 32px',
    borderBottom: '1px solid #e9ecef',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const contentStyle: React.CSSProperties = {
    padding: 32,
  };

  const logoStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '0 24px 24px',
    borderBottom: '1px solid rgba(255,255,255,0.15)',
    marginBottom: 16,
  };

  return (
    <div style={containerStyle}>
      <nav style={sidebarStyle}>
        <div style={logoStyle}>
          <Leaf size={28} color="#95d5b2" />
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>{t('app.title')}</div>
            <div style={{ fontSize: 11, opacity: 0.7 }}>{t('app.subtitle')}</div>
          </div>
        </div>
        {navItems.map(({ path, icon: Icon, labelKey }) => {
          const isActive = location.pathname === path;
          return (
            <NavLink
              key={path}
              to={path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 24px',
                color: 'white',
                textDecoration: 'none',
                background: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
                borderLeft: isRTL ? 'none' : isActive ? '3px solid #95d5b2' : '3px solid transparent',
                borderRight: isRTL ? (isActive ? '3px solid #95d5b2' : '3px solid transparent') : 'none',
                fontSize: 14,
                fontWeight: isActive ? 600 : 400,
                transition: 'all 0.2s',
              }}
            >
              <Icon size={20} />
              <span>{t(labelKey)}</span>
            </NavLink>
          );
        })}
      </nav>

      <div style={mainStyle}>
        <header style={headerStyle}>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: '#1b4332' }}>
            {t(navItems.find((n) => n.path === location.pathname)?.labelKey || 'nav.dashboard')}
          </h1>
          <button
            onClick={toggleLanguage}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 16px',
              border: '1px solid #dee2e6',
              borderRadius: 8,
              background: 'white',
              cursor: 'pointer',
              fontSize: 14,
              color: '#495057',
            }}
          >
            <Globe size={16} />
            {i18n.language === 'ar' ? 'English' : 'العربية'}
          </button>
        </header>
        <div style={contentStyle}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default App;
