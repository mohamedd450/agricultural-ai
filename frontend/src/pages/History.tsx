import React from 'react';
import { useTranslation } from 'react-i18next';
import HistoryPanel from '../components/HistoryPanel';

const History: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 600, color: '#1b4332', marginBottom: 24 }}>{t('history.title')}</h2>
      <HistoryPanel />
    </div>
  );
};

export default History;
