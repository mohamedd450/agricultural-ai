import React, { useCallback } from "react";
import { useTranslation } from "react-i18next";
import useVoice from "../hooks/useVoice";

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  isProcessing: boolean;
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
    padding: 24,
  },
  recordButton: {
    width: 72,
    height: 72,
    borderRadius: "50%",
    border: "none",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 28,
    transition: "transform 0.15s, box-shadow 0.15s",
    boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
  },
  idle: {
    backgroundColor: "#3b82f6",
    color: "#fff",
  },
  recording: {
    backgroundColor: "#ef4444",
    color: "#fff",
    animation: "pulse 1.2s ease-in-out infinite",
  },
  disabled: {
    backgroundColor: "#94a3b8",
    color: "#fff",
    cursor: "not-allowed",
    opacity: 0.7,
  },
  indicator: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 14,
    fontWeight: 600,
    color: "#ef4444",
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    backgroundColor: "#ef4444",
    animation: "pulse 1s ease-in-out infinite",
  },
  transcript: {
    width: "100%",
    maxWidth: 480,
    padding: 16,
    background: "#f1f5f9",
    borderRadius: 8,
    fontSize: 14,
    color: "#1e293b",
    lineHeight: 1.6,
    textAlign: "center",
  },
  processing: {
    fontSize: 14,
    color: "#64748b",
  },
  label: {
    fontSize: 13,
    color: "#94a3b8",
  },
};

const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, isProcessing }) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === "ar";
  const {
    isRecording,
    transcript,
    isProcessing: hookProcessing,
    startRecording,
    stopRecording,
    processVoice,
  } = useVoice();

  const busy = isProcessing || hookProcessing;

  const handleToggle = useCallback(async () => {
    if (busy) return;

    if (isRecording) {
      stopRecording();
      // Small delay to let the blob assemble, then process
      setTimeout(async () => {
        const result = await processVoice(i18n.language);
        if (result?.text_response) {
          onTranscript(result.text_response);
        }
      }, 300);
    } else {
      await startRecording();
    }
  }, [isRecording, busy, stopRecording, startRecording, processVoice, onTranscript, i18n.language]);

  const buttonStyle: React.CSSProperties = {
    ...styles.recordButton,
    ...(busy ? styles.disabled : isRecording ? styles.recording : styles.idle),
  };

  return (
    <div style={{ ...styles.container, direction: isRTL ? "rtl" : "ltr" }}>
      <button
        type="button"
        onClick={handleToggle}
        disabled={busy}
        style={buttonStyle}
        aria-label={isRecording ? t("voice.stop") : t("voice.record")}
      >
        {isRecording ? "⏹" : "🎤"}
      </button>

      {isRecording && (
        <div style={styles.indicator}>
          <span style={styles.dot} />
          {t("voice.recording")}
        </div>
      )}

      {!isRecording && !busy && (
        <div style={styles.label}>{t("voice.record")}</div>
      )}

      {busy && !isRecording && (
        <div style={styles.processing}>{t("voice.processing")}</div>
      )}

      {transcript && (
        <div style={styles.transcript}>{transcript}</div>
      )}
    </div>
  );
};

export default VoiceInput;
