import type {
  ChatHistoryMessage,
  ChatResponse,
  ResolvedKingIAskWidgetConfig,
  SourceSnippet,
} from "./types";

// 流式问答回调：chunk 逐段追加，sources 在回答生成完成后返回，done 结束。
export type StreamCallbacks = {
  onChunk: (content: string) => void;
  onSources: (sources: SourceSnippet[]) => void;
  onDone: (conversationSummary: string, standaloneQuestion: string) => void;
};

// 把后端返回的手册相对图片路径转换为可访问的静态资源 URL。
export function buildManualImageUrl(config: ResolvedKingIAskWidgetConfig, imagePath: string): string {
  if (/^https?:\/\//i.test(imagePath)) {
    return imagePath;
  }
  return `${config.apiBaseUrl}/manuals/${imagePath.replace(/^\/+/, "")}`;
}

// 把 RAG 来源 Markdown 路径转换成 Rspress 文档页面路径。
export function buildManualPageUrl(sourcePath: string): string | null {
  const normalized = sourcePath.replace(/\\/g, "/").replace(/^\/+/, "");
  if (!normalized.toLowerCase().endsWith(".md")) {
    return null;
  }

  const withoutProjectPrefix = normalized.replace(/^(helperFront\/docs\/|helperFront\/|docs\/)/, "");
  const withoutExtension = withoutProjectPrefix.replace(/\.md$/i, "");
  return `/${withoutExtension}`;
}

// 调用 KingIAsk RAG 问答接口，统一处理超时、认证、网络错误和连续对话上下文。
export async function askKingIAsk(
  config: ResolvedKingIAskWidgetConfig,
  question: string,
  conversationSummary = "",
  recentMessages: ChatHistoryMessage[] = [],
  conversationTurnCount = 0,
): Promise<ChatResponse> {
  if (!config.apiBaseUrl) {
    throw new Error("助手配置缺少服务地址。");
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), config.timeoutMs);
  const headers = new Headers({ "Content-Type": "application/json" });
  if (config.apiKey.trim()) {
    headers.set("X-API-Key", config.apiKey.trim());
  }
  const body: Record<string, unknown> = { question };
  if (conversationSummary.trim()) {
    body.conversation_summary = conversationSummary;
  }
  if (conversationTurnCount > 0) {
    body.conversation_turn_count = conversationTurnCount;
  }
  if (recentMessages.length > 0) {
    body.recent_messages = recentMessages;
  }

  try {
    const response = await fetch(`${config.apiBaseUrl}/api/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal
    });
    if (response.status === 401 || response.status === 403) {
      throw new Error("助手认证失败，请检查配置。");
    }
    if (!response.ok) {
      throw new Error("助手暂时不可用，请稍后再试。");
    }
    return (await response.json()) as ChatResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("请求超时，请稍后重试。");
    }
    if (error instanceof Error && error.message.startsWith("助手")) {
      throw error;
    }
    throw new Error("助手暂时不可用，请稍后再试。");
  } finally {
    window.clearTimeout(timeout);
  }
}

// 流式调用 RAG 问答接口（SSE），逐段回调回答内容，最后返回来源与多轮摘要。
// 服务端事件为单行 JSON：{"type": "chunk"|"answer"|"sources"|"done"|"error", ...}。
export async function askKingIAskStream(
  config: ResolvedKingIAskWidgetConfig,
  question: string,
  conversationSummary = "",
  recentMessages: ChatHistoryMessage[] = [],
  conversationTurnCount = 0,
  callbacks: StreamCallbacks,
): Promise<void> {
  if (!config.apiBaseUrl) {
    throw new Error("助手配置缺少服务地址。");
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), config.timeoutMs);
  const headers = new Headers({ "Content-Type": "application/json" });
  if (config.apiKey.trim()) {
    headers.set("X-API-Key", config.apiKey.trim());
  }
  const body: Record<string, unknown> = { question };
  if (conversationSummary.trim()) {
    body.conversation_summary = conversationSummary;
  }
  if (conversationTurnCount > 0) {
    body.conversation_turn_count = conversationTurnCount;
  }
  if (recentMessages.length > 0) {
    body.recent_messages = recentMessages;
  }

  try {
    const response = await fetch(`${config.apiBaseUrl}/api/chat/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (response.status === 401 || response.status === 403) {
      throw new Error("助手认证失败，请检查配置。");
    }
    if (!response.ok) {
      throw new Error("助手暂时不可用，请稍后再试。");
    }
    if (!response.body) {
      throw new Error("助手暂时不可用，请稍后再试。");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const event of events) {
        const dataLine = event.split("\n").find((line) => line.startsWith("data:"));
        if (!dataLine) {
          continue;
        }
        const data = dataLine.slice(5).trim();
        if (data === "[DONE]") {
          return;
        }
        let payload: Record<string, unknown>;
        try {
          payload = JSON.parse(data) as Record<string, unknown>;
        } catch {
          continue;
        }
        switch (payload.type) {
          case "chunk":
          case "answer":
            callbacks.onChunk(String(payload.content ?? ""));
            break;
          case "sources":
            callbacks.onSources(Array.isArray(payload.sources) ? (payload.sources as SourceSnippet[]) : []);
            break;
          case "done":
            callbacks.onDone(String(payload.conversation_summary ?? ""), String(payload.standalone_question ?? ""));
            break;
          case "error": {
            const serverMessage = String(payload.message ?? "助手暂时不可用，请稍后再试。");
            const serverError = new Error(serverMessage) as Error & { fromServer?: boolean };
            serverError.fromServer = true;
            throw serverError;
          }
          default:
            break;
        }
      }
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("请求超时，请稍后重试。");
    }
    if (error instanceof Error && (error as Error & { fromServer?: boolean }).fromServer) {
      throw error;
    }
    if (error instanceof Error && error.message.startsWith("助手")) {
      throw error;
    }
    throw new Error("助手暂时不可用，请稍后再试。");
  } finally {
    window.clearTimeout(timeout);
  }
}
