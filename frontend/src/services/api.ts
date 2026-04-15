import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from "axios";

// ── Interfaces ──────────────────────────────────────────────────────────────

export interface DiagnosisResponse {
  diagnosis: string;
  treatment: string;
  confidence: number;
  graph_paths: string[];
  explanation: string;
  source: string;
  language: string;
  timestamp: string;
}

export interface VoiceResponse {
  text_response: string;
  audio_url: string | null;
  diagnosis: DiagnosisResponse | null;
}

export interface AnalysisHistoryItem {
  id: string;
  query: string;
  diagnosis: string;
  confidence: number;
  timestamp: string;
}

export interface HistoryResponse {
  items: AnalysisHistoryItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface HealthStatus {
  status: string;
  services: Record<string, string>;
  timestamp: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ErrorResponse {
  detail: string;
  error_code: string;
  timestamp: string;
}

// ── Axios instance ──────────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL:
    process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("auth_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Centralised error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ErrorResponse>) => {
    if (error.response) {
      const { status } = error.response;

      if (status === 401) {
        localStorage.removeItem("auth_token");
        window.location.href = "/login";
      }

      const message =
        error.response.data?.detail || error.message || "Request failed";
      return Promise.reject(new Error(message));
    }

    if (error.request) {
      return Promise.reject(new Error("Network error – server unreachable"));
    }

    return Promise.reject(error);
  }
);

// ── API functions ───────────────────────────────────────────────────────────

export async function analyzeImage(
  file: File,
  textQuery?: string,
  language?: string
): Promise<DiagnosisResponse> {
  const formData = new FormData();
  formData.append("image", file);
  if (textQuery) formData.append("text_query", textQuery);
  if (language) formData.append("language", language);

  const { data } = await api.post<DiagnosisResponse>("/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function analyzeText(
  query: string,
  language?: string
): Promise<DiagnosisResponse> {
  const { data } = await api.post<DiagnosisResponse>("/text-query", {
    query,
    language: language ?? "ar",
  });
  return data;
}

export async function processVoice(
  audioBlob: Blob,
  language?: string
): Promise<VoiceResponse> {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  if (language) formData.append("language", language);

  const { data } = await api.post<VoiceResponse>("/voice", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getHistory(
  page?: number,
  perPage?: number
): Promise<HistoryResponse> {
  const { data } = await api.get<HistoryResponse>("/history", {
    params: { page, per_page: perPage },
  });
  return data;
}

export async function submitFeedback(
  analysisId: string,
  rating: number,
  comment?: string
): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>("/feedback", {
    analysis_id: analysisId,
    rating,
    comment,
  });
  return data;
}

export async function login(
  username: string,
  password: string
): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", {
    username,
    password,
  });
  return data;
}

export async function checkHealth(): Promise<HealthStatus> {
  const { data } = await api.get<HealthStatus>("/health/", {
    baseURL: process.env.REACT_APP_API_URL
      ? process.env.REACT_APP_API_URL.replace(/\/api\/v1\/?$/, "")
      : "http://localhost:8000",
  });
  return data;
}

export default api;
