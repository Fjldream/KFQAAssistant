import { afterEach, describe, expect, it, vi } from "vitest";
import type { ResolvedKingIAskWidgetConfig } from "./types";
import { askKingIAsk, askKingIAskStream, buildManualImageUrl, buildManualPageUrl } from "./api";

const baseConfig: ResolvedKingIAskWidgetConfig = {
  enabled: true,
  apiBaseUrl: "http://rag.local:8000",
  apiKey: "test-key",
  title: "KingIAsk",
  welcomeText: "欢迎",
  position: "right-bottom",
  timeoutMs: 5000,
  persistSession: true,
  accentColor: "",
  suggestedQuestions: []
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

  it("sends conversation summary and recent messages", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ answer: "回答", sources: [], conversation_summary: "新摘要" })
    });
    vi.stubGlobal("fetch", fetchMock);

    await askKingIAsk(baseConfig, "那怎么运行？", "旧摘要", [{ role: "user", content: "如何创建采集工程？" }], 1);

    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({
      question: "那怎么运行？",
      conversation_summary: "旧摘要",
      conversation_turn_count: 1,
      recent_messages: [{ role: "user", content: "如何创建采集工程？" }]
    });
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

describe("buildManualPageUrl", () => {
  it("maps helperFront markdown paths to documentation pages", () => {
    expect(buildManualPageUrl("helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置.md")).toBe(
      "/入门指南/2_从零搭建一个KF工程/2_数据采集配置"
    );
  });

  it("maps docs markdown paths to documentation pages", () => {
    expect(buildManualPageUrl("docs/详细教程/2_KF开发中心/6_数采管理/数采管理.md")).toBe(
      "/详细教程/2_KF开发中心/6_数采管理/数采管理"
    );
  });

  it("returns null for non-markdown paths", () => {
    expect(buildManualPageUrl("helperFront/入门指南/image/1.png")).toBeNull();
  });
});

describe("askKingIAskStream", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("parses SSE events and invokes callbacks in order", async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const events = [
          'data: {"type":"chunk","content":"点击"}\n\n',
          'data: {"type":"chunk","content":"新建。"}\n\n',
          'data: {"type":"sources","sources":[{"title":"采集工程"}]}\n\n',
          'data: {"type":"done","conversation_summary":"新摘要","standalone_question":"如何运行？"}\n\n',
          "data: [DONE]\n\n"
        ];
        events.forEach((event) => controller.enqueue(encoder.encode(event)));
        controller.close();
      }
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, body: stream }));

    const chunks: string[] = [];
    const callbacks = {
      onChunk: (content: string) => chunks.push(content),
      onSources: vi.fn(),
      onDone: vi.fn()
    };
    await askKingIAskStream(baseConfig, "问题", "", [], 0, callbacks);

    expect(chunks).toEqual(["点击", "新建。"]);
    expect(callbacks.onSources).toHaveBeenCalledWith([{ title: "采集工程" }]);
    expect(callbacks.onDone).toHaveBeenCalledWith("新摘要", "如何运行？");
  });

  it("throws a friendly error when the server emits an error event", async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"type":"error","message":"服务暂时不可用"}\n\n'));
        controller.close();
      }
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, body: stream }));

    const callbacks = { onChunk: () => {}, onSources: () => {}, onDone: () => {} };
    await expect(askKingIAskStream(baseConfig, "问题", "", [], 0, callbacks)).rejects.toThrow(
      "服务暂时不可用"
    );
  });
});
