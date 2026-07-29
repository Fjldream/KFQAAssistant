export interface ChatRequest {
  question: string;
}

export interface SourceSnippet {
  title: string;
  source_path: string;
  snippet: string;
  evidence_ids: string[];
  images: string[];
  score: number | null;
}

export interface ChatResponse {
  answer: string;
  sources: SourceSnippet[];
}

export interface HealthResponse {
  status: "ok";
}

export interface ReadinessResponse {
  status: "ready" | "not_ready";
  checks: Record<string, string>;
  issues: string[];
  chunks: number;
}

export interface IndexStatusResponse {
  status: "ready" | "empty" | "stale" | "error" | "rebuild_required";
  chunks: number;
  documents: number;
  last_built_at: string | null;
  index_signature: string | null;
  current_signature: string;
  config_matches: boolean;
  rebuild_pending: boolean;
  persist_dir: string;
  manifest_path: string;
  issue: string | null;
}

export interface ApiSettings {
  apiBaseUrl: string;
  apiKey: string;
}
