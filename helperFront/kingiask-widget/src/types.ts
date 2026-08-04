export type WidgetPosition = 'right-bottom' | 'left-bottom';

export type KingIAskWidgetConfig = {
  enabled: boolean;
  apiBaseUrl: string;
  apiKey?: string;
  title?: string;
  welcomeText?: string;
  position?: WidgetPosition;
  timeoutMs?: number;
  persistSession?: boolean;
  /** 品牌主色，例如 "#0071e3"，会覆盖默认 Apple 蓝。 */
  accentColor?: string;
  /** 欢迎页推荐问题，最多展示 4 个。 */
  suggestedQuestions?: string[];
};

export type ResolvedKingIAskWidgetConfig = Required<KingIAskWidgetConfig>;

export type SourceSnippet = {
  title: string;
  source_path: string;
  snippet: string;
  evidence_ids: string[];
  images: string[];
  score: number | null;
};

export type ChatRole = "user" | "assistant";

export type ChatHistoryMessage = {
  role: ChatRole;
  content: string;
};

export type ChatResponse = {
  answer: string;
  sources: SourceSnippet[];
  conversation_summary?: string;
  standalone_question?: string;
};

export type KingIAskWidgetApi = {
  init: (config?: Partial<KingIAskWidgetConfig>) => void;
  destroy: () => void;
};

declare global {
  interface Window {
    KINGIASK_WIDGET_CONFIG?: Partial<KingIAskWidgetConfig>;
    KingIAskWidget?: KingIAskWidgetApi;
  }
}
