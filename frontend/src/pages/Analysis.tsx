import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Send } from 'lucide-react';
import ImageUpload from '../components/ImageUpload';
import VoiceInput from '../components/VoiceInput';
import DiagnosisDisplay from '../components/DiagnosisDisplay';
import GraphVisualization from '../components/GraphVisualization';
import { useAnalysis } from '../hooks/useAnalysis';
import { useGraph } from '../hooks/useGraph';

const Analysis: React.FC = () => {
  const { t } = useTranslation();
  const [textInput, setTextInput] = useState('');
  const { result, loading, error, analyzeImage, analyzeText } = useAnalysis();
  const { graph, buildGraph } = useGraph();

  React.useEffect(() => {
    if (result?.diagnosis?.graph_paths) {
      buildGraph(result.diagnosis.graph_paths);
    }
  }, [result, buildGraph]);

  const handleImageUpload = (files: File[]) => {
    if (files.length > 0) analyzeImage(files[0], textInput || undefined);
  };

  const handleTextSubmit = () => {
    if (textInput.trim()) analyzeText(textInput.trim());
  };

  const card: React.CSSProperties = { background: 'white', borderRadius: 12, padding: 24, border: '1px solid #e9ecef', marginBottom: 24 };
  const sectionTitle: React.CSSProperties = { fontSize: 16, fontWeight: 600, color: '#1b4332', marginBottom: 16 };

  return (
    <div>
      <div style={card}>
        <h3 style={sectionTitle}>{t('analysis.imageUpload')}</h3>
        <ImageUpload onUpload={handleImageUpload} loading={loading} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div style={card}>
          <h3 style={sectionTitle}>{t('analysis.voiceInput')}</h3>
          <VoiceInput onTranscription={(text) => setTextInput(text)} />
        </div>
        <div style={card}>
          <h3 style={sectionTitle}>{t('analysis.textQuery')}</h3>
          <textarea value={textInput} onChange={(e) => setTextInput(e.target.value)} placeholder={t('analysis.textPlaceholder')} style={{ width: '100%', minHeight: 80, padding: 12, border: '1px solid #dee2e6', borderRadius: 8, fontSize: 14, resize: 'vertical', outline: 'none' }} />
          <button onClick={handleTextSubmit} disabled={loading || !textInput.trim()} style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 8, padding: '10px 24px', background: loading ? '#adb5bd' : '#2d6a4f', color: 'white', border: 'none', borderRadius: 8, cursor: loading ? 'not-allowed' : 'pointer', fontSize: 14, fontWeight: 600 }}>
            <Send size={16} />
            {loading ? t('analysis.analyzing') : t('analysis.analyze')}
          </button>
        </div>
      </div>
      {error && <div style={{ padding: 16, background: '#ffe0e0', borderRadius: 8, color: '#e63946', marginBottom: 24 }}>{error}</div>}
      {result && (
        <>
          <h3 style={{ ...sectionTitle, marginBottom: 16, marginTop: 8 }}>{t('analysis.results')}</h3>
          <div style={{ marginBottom: 24 }}><DiagnosisDisplay diagnosis={result.diagnosis} /></div>
          <h3 style={sectionTitle}>{t('analysis.graphPaths')}</h3>
          <GraphVisualization graph={graph} />
        </>
      )}
      {!result && !loading && !error && (
        <div style={{ textAlign: 'center', padding: 40, color: '#868e96' }}>{t('analysis.noResults')}</div>
      )}
    </div>
  );
};

export default Analysis;
