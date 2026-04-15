import React from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, MicOff, Loader } from 'lucide-react';
import { useVoice } from '../hooks/useVoice';

interface VoiceInputProps {
  onTranscription?: (text: string) => void;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscription }) => {
  const { t } = useTranslation();
  const { isRecording, isProcessing, transcription, error, startRecording, stopRecording } =
    useVoice();

  React.useEffect(() => {
    if (transcription && onTranscription) {
      onTranscription(transcription);
    }
  }, [transcription, onTranscription]);

  const buttonStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '12px 24px',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 600,
    color: 'white',
    background: isRecording ? '#e63946' : '#2d6a4f',
    transition: 'all 0.2s',
  };

  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
    return (
      <div style={{ color: '#868e96', fontSize: 14, padding: 16 }}>
        {t('voice.notSupported')}
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        style={{
          ...buttonStyle,
          opacity: isProcessing ? 0.6 : 1,
          cursor: isProcessing ? 'not-allowed' : 'pointer',
        }}
      >
        {isProcessing ? (
          <Loader size={18} style={{ animation: 'spin 1s linear infinite' }} />
        ) : isRecording ? (
          <MicOff size={18} />
        ) : (
          <Mic size={18} />
        )}
        {isProcessing
          ? t('voice.processing')
          : isRecording
          ? t('voice.stop')
          : t('voice.record')}
      </button>

      {isRecording && (
        <div
          style={{
            marginTop: 12,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            color: '#e63946',
            fontSize: 14,
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: '#e63946',
              animation: 'pulse 1s ease-in-out infinite',
            }}
          />
          {t('voice.recording')}
        </div>
      )}

      {transcription && (
        <div
          style={{
            marginTop: 12,
            padding: 12,
            background: '#f8f9fa',
            borderRadius: 8,
            border: '1px solid #e9ecef',
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 600, color: '#868e96', marginBottom: 4 }}>
            {t('voice.transcription')}
          </div>
          <div style={{ fontSize: 14, color: '#212529' }}>{transcription}</div>
        </div>
      )}

      {error && (
        <div style={{ marginTop: 8, color: '#e63946', fontSize: 13 }}>{error}</div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default VoiceInput;
