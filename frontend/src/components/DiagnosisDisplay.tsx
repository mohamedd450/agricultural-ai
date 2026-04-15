import React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';
import { DiagnosisResult } from '../services/api';

interface DiagnosisDisplayProps {
  diagnosis: DiagnosisResult;
}

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return '#2d6a4f';
  if (confidence >= 0.5) return '#e9c46a';
  return '#e63946';
};

const getConfidenceIcon = (confidence: number) => {
  if (confidence >= 0.8) return <CheckCircle size={18} color="#2d6a4f" />;
  if (confidence >= 0.5) return <AlertTriangle size={18} color="#e9c46a" />;
  return <AlertCircle size={18} color="#e63946" />;
};

const getConfidenceLabel = (confidence: number, t: (key: string) => string): string => {
  if (confidence >= 0.8) return t('diagnosis.high');
  if (confidence >= 0.5) return t('diagnosis.medium');
  return t('diagnosis.low');
};

const DiagnosisDisplay: React.FC<DiagnosisDisplayProps> = ({ diagnosis }) => {
  const { t } = useTranslation();
  const color = getConfidenceColor(diagnosis.confidence);

  const cardStyle: React.CSSProperties = {
    background: 'white',
    borderRadius: 12,
    padding: 24,
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
    border: '1px solid #e9ecef',
  };

  const sectionStyle: React.CSSProperties = {
    marginBottom: 20,
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 13,
    fontWeight: 600,
    color: '#868e96',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  };

  return (
    <div style={cardStyle}>
      {/* Disease Name */}
      <div style={sectionStyle}>
        <div style={labelStyle}>{t('diagnosis.disease')}</div>
        <div style={{ fontSize: 20, fontWeight: 700, color: '#1b4332' }}>
          {diagnosis.disease_name}
        </div>
      </div>

      {/* Confidence Bar */}
      <div style={sectionStyle}>
        <div style={{ ...labelStyle, display: 'flex', alignItems: 'center', gap: 6 }}>
          {getConfidenceIcon(diagnosis.confidence)}
          {t('diagnosis.confidence')}: {(diagnosis.confidence * 100).toFixed(1)}% —{' '}
          {getConfidenceLabel(diagnosis.confidence, t)}
        </div>
        <div
          style={{
            width: '100%',
            height: 8,
            background: '#e9ecef',
            borderRadius: 4,
            overflow: 'hidden',
            marginTop: 6,
          }}
        >
          <div
            style={{
              width: `${diagnosis.confidence * 100}%`,
              height: '100%',
              background: color,
              borderRadius: 4,
              transition: 'width 0.5s ease',
            }}
          />
        </div>
      </div>

      {/* Treatment */}
      <div style={sectionStyle}>
        <div style={labelStyle}>{t('diagnosis.treatment')}</div>
        <div
          style={{
            padding: 16,
            background: '#f0faf4',
            borderRadius: 8,
            color: '#1b4332',
            lineHeight: 1.6,
            fontSize: 14,
          }}
        >
          {diagnosis.treatment}
        </div>
      </div>

      {/* Explanation */}
      {diagnosis.explanation && (
        <div style={sectionStyle}>
          <div style={labelStyle}>{t('diagnosis.explanation')}</div>
          <div style={{ color: '#495057', lineHeight: 1.6, fontSize: 14 }}>
            {diagnosis.explanation}
          </div>
        </div>
      )}

      {/* Graph Paths Summary */}
      {diagnosis.graph_paths && diagnosis.graph_paths.length > 0 && (
        <div>
          <div style={labelStyle}>{t('diagnosis.graphPaths')}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {diagnosis.graph_paths.map((path, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 10px',
                  background: '#f1f3f5',
                  borderRadius: 6,
                  fontSize: 12,
                }}
              >
                {path.nodes.map((node, nIdx) => (
                  <React.Fragment key={node.id}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: 4,
                        background:
                          node.type === 'Disease'
                            ? '#ffe0e0'
                            : node.type === 'Symptom'
                            ? '#fff3cd'
                            : node.type === 'Crop'
                            ? '#d4edda'
                            : '#cce5ff',
                        fontSize: 11,
                        fontWeight: 500,
                      }}
                    >
                      {node.label}
                    </span>
                    {nIdx < path.nodes.length - 1 && (
                      <span style={{ color: '#adb5bd' }}>→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagnosisDisplay;
