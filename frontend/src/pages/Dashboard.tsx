import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Upload, Clock, Activity, CheckCircle, XCircle } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const card: React.CSSProperties = { background: 'white', borderRadius: 12, padding: 24, border: '1px solid #e9ecef' };
  const statusDot = (online: boolean): React.CSSProperties => ({
    width: 10, height: 10, borderRadius: '50%', background: online ? '#2d6a4f' : '#e63946',
  });

  return (
    <div>
      <div style={{ ...card, marginBottom: 24, background: 'linear-gradient(135deg, #d8f3dc 0%, #b7e4c7 100%)', border: 'none' }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: '#1b4332', marginBottom: 8 }}>{t('dashboard.welcome')}</h2>
        <p style={{ color: '#40916c', lineHeight: 1.6 }}>{t('dashboard.welcomeDesc')}</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
        <div style={card}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <Upload size={24} color="#2d6a4f" />
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>{t('dashboard.quickAnalysis')}</h3>
          </div>
          <p style={{ color: '#868e96', fontSize: 14, marginBottom: 16 }}>{t('dashboard.quickAnalysisDesc')}</p>
          <button onClick={() => navigate('/analysis')} style={{ padding: '10px 24px', background: '#2d6a4f', color: 'white', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: 14 }}>
            {t('dashboard.startAnalysis')}
          </button>
        </div>
        <div style={card}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <Clock size={24} color="#457b9d" />
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>{t('dashboard.recentAnalyses')}</h3>
          </div>
          <p style={{ color: '#868e96', fontSize: 14 }}>{t('dashboard.noRecent')}</p>
        </div>
        <div style={card}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <Activity size={24} color="#e9c46a" />
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>{t('dashboard.systemStatus')}</h3>
          </div>
          {[{ key: 'apiStatus', online: true }, { key: 'modelStatus', online: true }, { key: 'graphStatus', online: true }].map(({ key, online }) => (
            <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f1f3f5' }}>
              <span style={{ fontSize: 14, color: '#495057' }}>{t(`dashboard.${key}`)}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={statusDot(online)} />
                <span style={{ fontSize: 13, color: online ? '#2d6a4f' : '#e63946' }}>{t(online ? 'dashboard.online' : 'dashboard.offline')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
