import { afterEach, describe, expect, it, vi } from "vitest";
import type { ResolvedKingIAskWidgetConfig } from "./types";
import { askKingIAsk, buildManualImageUrl } from "./api";

const baseConfig: ResolvedKingIAskWidgetConfig = {
  enabled: true,
  apiBaseUrl: "http://rag.local:8000",
  apiKey: "test-key",
  title: "KingIAsk",
  welcomeText: "欢迎",
  position: "right-bottom",
  timeoutMs: 5000
};

describe("askKingIAsk", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("posts the question to the configured chat endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "回答", sources: [] })
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await askKingIAsk(baseConfig, "如何创建采集工程？");

    expect(response.answer).toBe("回答");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://rag.local:8000/api/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "如何创建采集工程？" })
      })
    );
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("X-API-Key")).toBe("test-key");
  });

  it("throws a friendly auth error for 401 or 403", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 403, statusText: "Forbidden" }));

    await expect(askKingIAsk(baseConfig, "问题")).rejects.toThrow("助手认证失败，请检查配置。");
  });

  it("omits the API key header when the configured key is blank", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "回答", sources: [] })
    });
    vi.stubGlobal("fetch", fetchMock);

    await askKingIAsk({ ...baseConfig, apiKey: "   " }, "问题");

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.has("X-API-Key")).toBe(false);
  });

  it("trims a non-empty API key before sending it", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "回答", sources: [] })
    });
    vi.stubGlobal("fetch", fetchMock);

    await askKingIAsk({ ...baseConfig, apiKey: "  trimmed-key  " }, "问题");

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("X-API-Key")).toBe("trimmed-key");
  });

  it("maps an AbortError to a friendly timeout and clears the timer", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn().mockImplementation((_input, init: RequestInit) =>
      new Promise((_, reject) => {
        init.signal?.addEventListener("abort", () => {
          reject(new DOMException("The operation was aborted.", "AbortError"));
        });
      })
    );
    vi.stubGlobal("fetch", fetchMock);
    const clearTimeoutSpy = vi.spyOn(window, "clearTimeout");
    const request = askKingIAsk(baseConfig, "问题");
    const timeoutAssertion = expect(request).rejects.toThrow("请求超时，请稍后重试。");

    await vi.advanceTimersByTimeAsync(baseConfig.timeoutMs);

    await timeoutAssertion;

    expect(clearTimeoutSpy).toHaveBeenCalledTimes(1);
  });

  it("maps a network rejection to a friendly unavailable error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    await expect(askKingIAsk(baseConfig, "问题")).rejects.toThrow("助手暂时不可用，请稍后再试。");
  });

  it("maps a non-authentication failure response to a friendly unavailable error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, statusText: "Internal Server Error" }));

    await expect(askKingIAsk(baseConfig, "问题")).rejects.toThrow("助手暂时不可用，请稍后再试。");
  });
});

describe("buildManualImageUrl", () => {
  it("keeps absolute image URLs unchanged", () => {
    expect(buildManualImageUrl(baseConfig, "https://example.com/a.png")).toBe("https://example.com/a.png");
  });

  it("maps relative manual images through the RAG static manual endpoint", () => {
    expect(buildManualImageUrl(baseConfig, "html/a/1.png")).toBe("http://rag.local:8000/manuals/html/a/1.png");
  });
});
