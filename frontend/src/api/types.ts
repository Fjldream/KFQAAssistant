export type ChatRole = "user" | "assistant";

export interface ChatHistoryMessage {
  role: ChatRole;
  content: string;
}

export interface ChatRequest {
  question: string;
  conversation_summary?: string;
  conversation_turn_count?: number;
  recent_messages?: ChatHistoryMessage[];
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
  conversation_summary?: string;
  standalone_question?: string;
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

export type ThemePreference = "light" | "dark" | "system";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  sources: SourceSnippet[];
  createdAt: string;
  /** 流式输出进行中：气泡显示打字光标，完成后置为 false。 */
  streaming?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  conversationSummary: string;
  messages: ChatMessage[];
}
