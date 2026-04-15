import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  analyzeImage as apiAnalyzeImage,
  textQuery as apiTextQuery,
  DiagnosisResponse,
} from '../services/api';

interface UseAnalysisReturn {
  result: DiagnosisResponse | null;
  loading: boolean;
  error: string | null;
  analyzeImage: (file: File, text?: string) => Promise<void>;
  analyzeText: (query: string) => Promise<void>;
  clear: () => void;
}

export const useAnalysis = (): UseAnalysisReturn => {
  const { i18n } = useTranslation();
  const [result, setResult] = useState<DiagnosisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeImage = useCallback(
    async (file: File, text?: string) => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiAnalyzeImage(file, text, i18n.language);
        setResult(response);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'Analysis failed';
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [i18n.language],
  );

  const analyzeText = useCallback(
    async (query: string) => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiTextQuery(query, i18n.language);
        setResult(response);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'Analysis failed';
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [i18n.language],
  );

  const clear = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, analyzeImage, analyzeText, clear };
};
