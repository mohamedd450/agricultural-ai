import { useState, useCallback } from "react";
import {
  analyzeImage as apiAnalyzeImage,
  analyzeText as apiAnalyzeText,
  DiagnosisResponse,
} from "../services/api";

interface UseAnalysisReturn {
  isLoading: boolean;
  result: DiagnosisResponse | null;
  error: string | null;
  analyzeImage: (file: File, textQuery?: string) => Promise<void>;
  analyzeText: (query: string) => Promise<void>;
  reset: () => void;
}

export default function useAnalysis(): UseAnalysisReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<DiagnosisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyzeImage = useCallback(
    async (file: File, textQuery?: string) => {
      setIsLoading(true);
      setError(null);
      setResult(null);
      try {
        const data = await apiAnalyzeImage(file, textQuery);
        setResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Image analysis failed");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const analyzeText = useCallback(async (query: string) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiAnalyzeText(query);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Text analysis failed");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsLoading(false);
    setResult(null);
    setError(null);
  }, []);

  return { isLoading, result, error, analyzeImage, analyzeText, reset };
}
