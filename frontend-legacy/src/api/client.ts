import type {
  ApiSettings,
  ChatRequest,
  ChatResponse,
  HealthResponse,
  IndexStatusResponse,
  ReadinessResponse,
} from "./types";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// 规范化 API 基础地址，避免用户在设置里多填斜杠导致请求路径错误。
export function normalizeApiBaseUrl(apiBaseUrl: string): string {
  return apiBaseUrl.replace(/\/+$/, "");
}

// 将后端返回的手册相对图片路径转换成浏览器可访问的图片地址。
export function resolveImageUrl(apiBaseUrl: string, imagePath: string): string {
  if (/^https?:\/\//i.test(imagePath)) {
    return imagePath;
  }
  return `${normalizeApiBaseUrl(apiBaseUrl)}/manuals/${imagePath.replace(/^\/+/, "")}`;
}

// 从后端错误响应中提取用户可读的错误信息。
async function parseError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return new ApiError(response.status, String(payload.detail ?? response.statusText));
  } catch {
    return new ApiError(response.status, response.statusText);
  }
}

// 封装所有后端请求，统一添加 API Key、解析 JSON 和转换错误。
async function requestJson<T>(settings: ApiSettings, path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (settings.apiKey.trim()) {
    headers.set("X-API-Key", settings.apiKey.trim());
  }

  const response = await fetch(`${normalizeApiBaseUrl(settings.apiBaseUrl)}${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as T;
}

// 创建面向 KingIAsk 页面使用的后端 API 客户端。
export function createApiClient(settings: ApiSettings) {
  return {
    health: () => requestJson<HealthResponse>(settings, "/api/health"),
    readiness: () => requestJson<ReadinessResponse>(settings, "/api/health/ready"),
    indexStatus: () => requestJson<IndexStatusResponse>(settings, "/api/index/status"),
    chat: (request: ChatRequest) =>
      requestJson<ChatResponse>(settings, "/api/chat", {
        method: "POST",
        body: JSON.stringify(request),
      }),
  };
}
