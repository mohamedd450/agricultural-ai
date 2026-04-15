/**
 * Core TypeScript type definitions for the Agricultural AI platform.
 * تعريفات TypeScript للمنصة الزراعية الذكية
 */

// ── Language ───────────────────────────────────────────────────────────────

export type LanguageCode = "ar" | "en";

// ── Analysis & Diagnosis ──────────────────────────────────────────────────

export interface ConfidenceBreakdown {
  vision: number;
  graph_rag: number;
  vector_db: number;
  fused: number;
}

export interface DiagnosisData {
  /** Identified disease or deficiency */
  diagnosis: string;
  /** Recommended treatment */
  treatment: string;
  /** Overall confidence score (0–1) */
  confidence: number;
  /** Explainable reasoning paths from the knowledge graph */
  graph_paths: string[];
  /** Human-readable explanation of how the result was derived */
  explanation: string;
  /** Primary knowledge source used */
  source: "vision" | "graph_rag" | "vector" | "combined" | "fallback";
  /** Response language */
  language: LanguageCode;
  /** ISO timestamp of analysis */
  timestamp: string;
  /** Detailed confidence breakdown per source */
  confidence_breakdown?: ConfidenceBreakdown;
}

export interface AnalysisResult {
  /** Unique analysis session identifier */
  session_id: string;
  /** The diagnosis data */
  data: DiagnosisData;
  /** Analysis was served from cache */
  from_cache?: boolean;
}

// ── Voice ─────────────────────────────────────────────────────────────────

export interface VoiceRecording {
  blob: Blob;
  duration: number;
  mimeType: string;
}

export interface SpeechToTextResult {
  text: string;
  language: LanguageCode;
  confidence: number;
}

export interface AudioResponse {
  audio: Blob;
  text: string;
  language: LanguageCode;
}

// ── Graph Visualisation ───────────────────────────────────────────────────

export type NodeType =
  | "disease"
  | "symptom"
  | "crop"
  | "fertilizer"
  | "treatment"
  | "weather";

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  properties?: Record<string, unknown>;
  x?: number;
  y?: number;
  size?: number;
  color?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ── History ───────────────────────────────────────────────────────────────

export interface HistoryItem {
  id: string;
  imageThumbnail?: string;
  diagnosis: string;
  confidence: number;
  language: LanguageCode;
  timestamp: string;
  fullResult?: DiagnosisData;
}

export interface FeedbackData {
  session_id: string;
  rating: number;
  comment?: string;
  is_correct?: boolean;
}

// ── Settings ──────────────────────────────────────────────────────────────

export interface UserSettings {
  language: LanguageCode;
  theme: "light" | "dark" | "system";
  maxImageSizeMB: number;
  enableRealtime: boolean;
  enableVoice: boolean;
}

// ── API ───────────────────────────────────────────────────────────────────

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  status: number;
}

export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  services: Record<string, "up" | "down" | "degraded">;
  version: string;
  timestamp: string;
}

// ── WebSocket ─────────────────────────────────────────────────────────────

export type WsMessageType =
  | "analysis_started"
  | "analysis_progress"
  | "analysis_complete"
  | "analysis_error"
  | "system_status"
  | "ping"
  | "pong";

export interface WsMessage {
  type: WsMessageType;
  session_id?: string;
  progress?: number;
  stage?: string;
  data?: DiagnosisData | ApiError | Record<string, unknown>;
  timestamp: string;
}

// ── State management ──────────────────────────────────────────────────────

export type AnalysisStatus =
  | "idle"
  | "uploading"
  | "processing"
  | "complete"
  | "error";

export interface AnalysisState {
  status: AnalysisStatus;
  result: AnalysisResult | null;
  error: string | null;
  progress: number;
  currentStage: string | null;
}
