import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, ChevronRight, Clock, Search } from 'lucide-react';
import { getHistory, HistoryItem, HistoryResponse } from '../services/api';

interface HistoryPanelProps {
  onSelectItem?: (item: HistoryItem) => void;
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({ onSelectItem }) => {
  const { t } = useTranslation();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  const fetchHistory = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const response: HistoryResponse = await getHistory(p);
      setHistory(response.items);
      setTotalPages(response.pages);
    } catch {
      // Silently handle — show empty state
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory(page);
  }, [page, fetchHistory]);

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return '#2d6a4f';
    if (confidence >= 0.5) return '#e9c46a';
    return '#e63946';
  };

  const cardStyle: React.CSSProperties = {
    background: 'white',
    borderRadius: 12,
    border: '1px solid #e9ecef',
    overflow: 'hidden',
  };

  if (loading) {
    return (
      <div style={{ ...cardStyle, padding: 40, textAlign: 'center', color: '#868e96' }}>
        Loading...
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div style={{ ...cardStyle, padding: 40, textAlign: 'center', color: '#868e96' }}>
        <Clock size={40} style={{ marginBottom: 12 }} />
        <p>{t('history.noHistory')}</p>
      </div>
    );
  }

  return (
    <div style={cardStyle}>
      {history.map((item, index) => (
        <div
          key={item.request_id}
          onClick={() => onSelectItem?.(item)}
          style={{
            padding: 16,
            borderBottom: index < history.length - 1 ? '1px solid #e9ecef' : 'none',
            cursor: onSelectItem ? 'pointer' : 'default',
            transition: 'background 0.15s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#f8f9fa';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'white';
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <Search size={14} color="#868e96" />
                <span style={{ fontSize: 13, color: '#868e96' }}>{t('history.query')}</span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 500, color: '#212529', marginBottom: 8 }}>
                {item.query}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13 }}>
                <span style={{ color: '#495057' }}>
                  <strong>{t('history.diagnosis')}:</strong> {item.diagnosis.disease_name}
                </span>
                <span style={{ color: getConfidenceColor(item.diagnosis.confidence) }}>
                  <strong>{t('history.confidence')}:</strong>{' '}
                  {(item.diagnosis.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div style={{ fontSize: 12, color: '#adb5bd', whiteSpace: 'nowrap' }}>
              {new Date(item.timestamp).toLocaleDateString()}
            </div>
          </div>
        </div>
      ))}

      {/* Pagination */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 16,
          padding: 16,
          borderTop: '1px solid #e9ecef',
          background: '#fafafa',
        }}
      >
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '6px 12px',
            border: '1px solid #dee2e6',
            borderRadius: 6,
            background: 'white',
            cursor: page <= 1 ? 'not-allowed' : 'pointer',
            opacity: page <= 1 ? 0.5 : 1,
            fontSize: 13,
          }}
        >
          <ChevronLeft size={14} /> {t('history.previous')}
        </button>
        <span style={{ fontSize: 13, color: '#495057' }}>
          {t('history.page')} {page} / {totalPages}
        </span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '6px 12px',
            border: '1px solid #dee2e6',
            borderRadius: 6,
            background: 'white',
            cursor: page >= totalPages ? 'not-allowed' : 'pointer',
            opacity: page >= totalPages ? 0.5 : 1,
            fontSize: 13,
          }}
        >
          {t('history.next')} <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
};

export default HistoryPanel;
