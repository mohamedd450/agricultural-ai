import axios, { AxiosInstance } from 'axios';

// ---------- Type definitions ----------

export interface DiagnosisResult {
  disease_name: string;
  confidence: number;
  treatment: string;
  explanation: string;
  graph_paths: GraphPath[];
}

export interface GraphPath {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'Disease' | 'Symptom' | 'Crop' | 'Treatment';
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface DiagnosisResponse {
  request_id: string;
  diagnosis: DiagnosisResult;
  language: string;
  timestamp: string;
}

export interface VoiceResponse {
  transcription: string;
  language: string;
  diagnosis: DiagnosisResult;
  request_id: string;
}

export interface HistoryItem {
  request_id: string;
  query: string;
  diagnosis: DiagnosisResult;
  timestamp: string;
  type: 'image' | 'voice' | 'text';
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  pages: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// ---------- API client ----------

const BASE_URL = process.env.REACT_APP_API_URL || '/api';

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: BASE_URL,
    timeout: 60000,
    headers: { 'Content-Type': 'application/json' },
  });

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/';
      }
      return Promise.reject(error);
    },
  );

  return client;
};

const api = createApiClient();

// ---------- API methods ----------

export const analyzeImage = async (
  file: File,
  text?: string,
  language: string = 'en',
): Promise<DiagnosisResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (text) formData.append('text', text);
  formData.append('language', language);

  const response = await api.post<DiagnosisResponse>('/analyze/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const analyzeVoice = async (audioBlob: Blob): Promise<VoiceResponse> => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');

  const response = await api.post<VoiceResponse>('/analyze/voice', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const textQuery = async (
  query: string,
  language: string = 'en',
): Promise<DiagnosisResponse> => {
  const response = await api.post<DiagnosisResponse>('/analyze/text', {
    query,
    language,
  });
  return response.data;
};

export const getHistory = async (page: number = 1): Promise<HistoryResponse> => {
  const response = await api.get<HistoryResponse>('/history', { params: { page } });
  return response.data;
};

export const submitFeedback = async (
  requestId: string,
  rating: number,
  comment?: string,
): Promise<void> => {
  await api.post('/feedback', { request_id: requestId, rating, comment });
};

export const login = async (
  username: string,
  password: string,
): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await api.post<TokenResponse>('/auth/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
};

export default api;
