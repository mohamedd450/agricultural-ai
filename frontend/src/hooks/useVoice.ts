import { useState, useRef, useCallback } from "react";
import { processVoice as apiProcessVoice, VoiceResponse } from "../services/api";

interface UseVoiceReturn {
  isRecording: boolean;
  audioBlob: Blob | null;
  transcript: string | null;
  isProcessing: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  processVoice: (language?: string) => Promise<VoiceResponse | null>;
  reset: () => void;
}

export default function useVoice(): UseVoiceReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    chunksRef.current = [];

    mediaRecorder.ondataavailable = (event: BlobEvent) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      setAudioBlob(blob);
      // Release microphone
      stream.getTracks().forEach((track) => track.stop());
    };

    mediaRecorder.start();
    setIsRecording(true);
  }, []);

  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const processVoice = useCallback(
    async (language?: string): Promise<VoiceResponse | null> => {
      if (!audioBlob) return null;

      setIsProcessing(true);
      try {
        const response = await apiProcessVoice(audioBlob, language);
        setTranscript(response.text_response);
        return response;
      } catch {
        setTranscript(null);
        return null;
      } finally {
        setIsProcessing(false);
      }
    },
    [audioBlob]
  );

  const reset = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setAudioBlob(null);
    setTranscript(null);
    setIsProcessing(false);
  }, []);

  return {
    isRecording,
    audioBlob,
    transcript,
    isProcessing,
    startRecording,
    stopRecording,
    processVoice,
    reset,
  };
}
