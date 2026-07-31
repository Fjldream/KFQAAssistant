export type WidgetPosition = 'right-bottom' | 'left-bottom';

export type KingIAskWidgetConfig = {
  enabled: boolean;
  apiBaseUrl: string;
  apiKey?: string;
  title?: string;
  welcomeText?: string;
  position?: WidgetPosition;
  timeoutMs?: number;
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

export type ChatResponse = {
  answer: string;
  sources: SourceSnippet[];
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
