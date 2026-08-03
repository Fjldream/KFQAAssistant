import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createApiClient, normalizeApiBaseUrl, resolveImageUrl } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("normalizeApiBaseUrl", () => {
  it("去除末尾斜杠", () => {
    expect(normalizeApiBaseUrl("http://127.0.0.1:8000/")).toBe("http://127.0.0.1:8000");
    expect(normalizeApiBaseUrl("http://127.0.0.1:8000///")).toBe("http://127.0.0.1:8000");
    expect(normalizeApiBaseUrl("http://127.0.0.1:8000")).toBe("http://127.0.0.1:8000");
  });
});

describe("resolveImageUrl", () => {
  it("相对路径拼接到 /manuals", () => {
    expect(resolveImageUrl("http://127.0.0.1:8000", "html/a/1.png")).toBe(
      "http://127.0.0.1:8000/manuals/html/a/1.png",
    );
  });

  it("绝对 URL 原样返回", () => {
    expect(resolveImageUrl("http://127.0.0.1:8000", "https://cdn.example.com/1.png")).toBe(
      "https://cdn.example.com/1.png",
    );
  });
});

describe("createApiClient", () => {
  it("chat 发送 POST 并携带 API Key", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "回答", sources: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient({ apiBaseUrl: "http://127.0.0.1:8000/", apiKey: "secret" });
    const result = await client.chat({ question: "hi" });

    expect(result.answer).toBe("回答");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8000/api/chat");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ question: "hi" }));
    const headers = new Headers(init.headers);
    expect(headers.get("X-API-Key")).toBe("secret");
  });

  it("非 2xx 抛出 ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        json: async () => ({ detail: "服务暂不可用" }),
      }),
    );

    const client = createApiClient({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    const error = await client.chat({ question: "hi" }).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(503);
    expect((error as ApiError).detail).toBe("服务暂不可用");
  });
});
