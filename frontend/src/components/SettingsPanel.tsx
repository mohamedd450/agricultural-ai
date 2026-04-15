import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Sun, Moon, Key, Eye, EyeOff, User, Save } from 'lucide-react';

const SettingsPanel: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [showApiKey, setShowApiKey] = useState(false);
  const [username, setUsername] = useState('farmer_user');
  const [email, setEmail] = useState('user@agricultural-ai.com');

  const apiKey = 'ak_xxxx-xxxx-xxxx-xxxx';

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
  };

  const cardStyle: React.CSSProperties = {
    background: 'white',
    borderRadius: 12,
    padding: 24,
    border: '1px solid #e9ecef',
    marginBottom: 24,
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 16,
    fontWeight: 600,
    color: '#212529',
  };

  const descStyle: React.CSSProperties = {
    fontSize: 13,
    color: '#868e96',
    marginBottom: 12,
  };

  const buttonGroupStyle: React.CSSProperties = {
    display: 'flex',
    gap: 8,
  };

  const optionButton = (active: boolean): React.CSSProperties => ({
    padding: '8px 20px',
    border: `1px solid ${active ? '#2d6a4f' : '#dee2e6'}`,
    borderRadius: 8,
    background: active ? '#2d6a4f' : 'white',
    color: active ? 'white' : '#495057',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: active ? 600 : 400,
    transition: 'all 0.2s',
  });

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    border: '1px solid #dee2e6',
    borderRadius: 8,
    fontSize: 14,
    marginBottom: 12,
    outline: 'none',
  };

  return (
    <div>
      {/* Language */}
      <div style={cardStyle}>
        <div style={headerStyle}>
          <Globe size={20} color="#2d6a4f" />
          <span style={labelStyle}>{t('settings.language')}</span>
        </div>
        <p style={descStyle}>{t('settings.languageDesc')}</p>
        <div style={buttonGroupStyle}>
          <button
            onClick={() => handleLanguageChange('en')}
            style={optionButton(i18n.language === 'en')}
          >
            {t('settings.english')}
          </button>
          <button
            onClick={() => handleLanguageChange('ar')}
            style={optionButton(i18n.language === 'ar')}
          >
            {t('settings.arabic')}
          </button>
        </div>
      </div>

      {/* Theme */}
      <div style={cardStyle}>
        <div style={headerStyle}>
          {theme === 'light' ? (
            <Sun size={20} color="#e9c46a" />
          ) : (
            <Moon size={20} color="#457b9d" />
          )}
          <span style={labelStyle}>{t('settings.theme')}</span>
        </div>
        <p style={descStyle}>{t('settings.themeDesc')}</p>
        <div style={buttonGroupStyle}>
          <button onClick={() => setTheme('light')} style={optionButton(theme === 'light')}>
            {t('settings.light')}
          </button>
          <button onClick={() => setTheme('dark')} style={optionButton(theme === 'dark')}>
            {t('settings.dark')}
          </button>
        </div>
      </div>

      {/* API Key */}
      <div style={cardStyle}>
        <div style={headerStyle}>
          <Key size={20} color="#e63946" />
          <span style={labelStyle}>{t('settings.apiKey')}</span>
        </div>
        <p style={descStyle}>{t('settings.apiKeyDesc')}</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <code
            style={{
              flex: 1,
              padding: '10px 14px',
              background: '#f1f3f5',
              borderRadius: 8,
              fontSize: 14,
              fontFamily: 'monospace',
              letterSpacing: showApiKey ? 0 : 2,
            }}
          >
            {showApiKey ? apiKey : '••••••••••••••••••••'}
          </code>
          <button
            onClick={() => setShowApiKey(!showApiKey)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '10px 16px',
              border: '1px solid #dee2e6',
              borderRadius: 8,
              background: 'white',
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
            {showApiKey ? t('settings.hide') : t('settings.show')}
          </button>
        </div>
      </div>

      {/* Profile */}
      <div style={cardStyle}>
        <div style={headerStyle}>
          <User size={20} color="#457b9d" />
          <span style={labelStyle}>{t('settings.profile')}</span>
        </div>
        <p style={descStyle}>{t('settings.profileDesc')}</p>
        <div>
          <label style={{ fontSize: 13, fontWeight: 500, color: '#495057', display: 'block', marginBottom: 4 }}>
            {t('settings.username')}
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={inputStyle}
          />
          <label style={{ fontSize: 13, fontWeight: 500, color: '#495057', display: 'block', marginBottom: 4 }}>
            {t('settings.email')}
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={inputStyle}
          />
          <button
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 24px',
              background: '#2d6a4f',
              color: 'white',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 600,
            }}
          >
            <Save size={16} />
            {t('settings.save')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
