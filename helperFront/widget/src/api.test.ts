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
});

describe("buildManualImageUrl", () => {
  it("keeps absolute image URLs unchanged", () => {
    expect(buildManualImageUrl(baseConfig, "https://example.com/a.png")).toBe("https://example.com/a.png");
  });

  it("maps relative manual images through the RAG static manual endpoint", () => {
    expect(buildManualImageUrl(baseConfig, "html/a/1.png")).toBe("http://rag.local:8000/manuals/html/a/1.png");
  });
});
