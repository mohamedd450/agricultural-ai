import React from 'react';
import { useTranslation } from 'react-i18next';
import SettingsPanel from '../components/SettingsPanel';

const Settings: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 600, color: '#1b4332', marginBottom: 24 }}>{t('settings.title')}</h2>
      <SettingsPanel />
    </div>
  );
};

export default Settings;
