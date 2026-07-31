import type { ChatResponse, ResolvedKingIAskWidgetConfig } from "./types";

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

// 调用 KingIAsk RAG 问答接口，统一处理超时、认证和网络错误。
export async function askKingIAsk(config: ResolvedKingIAskWidgetConfig, question: string): Promise<ChatResponse> {
  if (!config.apiBaseUrl) {
    throw new Error("助手配置缺少服务地址。");
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), config.timeoutMs);
  const headers = new Headers({ "Content-Type": "application/json" });
  if (config.apiKey.trim()) {
    headers.set("X-API-Key", config.apiKey.trim());
  }

  try {
    const response = await fetch(`${config.apiBaseUrl}/api/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({ question }),
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
