import { afterEach, describe, expect, it, vi } from "vitest";
import type { ResolvedKingIAskWidgetConfig, SourceSnippet } from "./types";
import { createKingIAskWidget } from "./widget";
import * as api from "./api";

const config: ResolvedKingIAskWidgetConfig = {
  enabled: true,
  apiBaseUrl: "http://rag.local:8000",
  apiKey: "",
  title: "KingIAsk",
  welcomeText: "欢迎使用助手",
  position: "right-bottom",
  timeoutMs: 60000,
  persistSession: true,
  accentColor: "",
  suggestedQuestions: []
};

const source: SourceSnippet = {
  title: "采集工程",
  source_path: "helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置.md",
  snippet: "# helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置\n\n点击新建工程。",
  evidence_ids: ["资料 1"],
  images: ["html/数采管理/1.png"],
  score: 0.9
};

// 用假流式实现替换网络层：逐段回调 chunk，再回传 sources 与摘要。
function mockStream(overrides: {
  chunks?: string[];
  sources?: SourceSnippet[];
  summary?: string;
  standalone?: string;
} = {}) {
  return vi.spyOn(api, "askKingIAskStream").mockImplementation(
    async (_config, _question, _summary, _messages, _turns, callbacks) => {
      for (const chunk of overrides.chunks ?? ["回答内容"]) {
        callbacks.onChunk(chunk);
      }
      callbacks.onSources(overrides.sources ?? []);
      callbacks.onDone(overrides.summary ?? "", overrides.standalone ?? "");
    },
  );
}

function hostRoot(): HTMLElement {
  return document.querySelector("[data-kingiask-widget-root]") as HTMLElement;
}

function openAndAsk(host: HTMLElement, question: string): void {
  host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']")?.click();
  const textarea = host.shadowRoot?.querySelector<HTMLTextAreaElement>("textarea[data-role='question']") as HTMLTextAreaElement;
  textarea.value = question;
  host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='send']")?.click();
}

describe("createKingIAskWidget", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    window.sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("does not render when disabled", () => {
    const instance = createKingIAskWidget({ ...config, enabled: false });

    expect(instance).toBeNull();
    expect(document.querySelector("[data-kingiask-widget-root]")).toBeNull();
  });

  it("renders a floating button and opens the panel", () => {
    createKingIAskWidget(config);

    const host = hostRoot();
    host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']")?.click();

    expect(host.shadowRoot?.textContent).toContain("KingIAsk");
    expect(host.shadowRoot?.textContent).toContain("欢迎使用助手");
  });

  it("renders a branded launcher and dialog shell", () => {
    createKingIAskWidget(config);

    const host = hostRoot();
    const launcher = host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']");
    const panel = host.shadowRoot?.querySelector<HTMLElement>("[data-role='panel']");

    expect(launcher?.getAttribute("aria-label")).toBe("打开 KingIAsk 助手");
    expect(launcher?.title).toContain("KingIAsk");
    expect(panel?.getAttribute("role")).toBe("dialog");
    expect(panel?.getAttribute("aria-labelledby")).toBe("kiw-title");
  });

  it("streams the answer chunk by chunk and renders sources and images", async () => {
    mockStream({ chunks: ["点击", "新建工程。"], sources: [source] });
    createKingIAskWidget(config);
    const host = hostRoot();
    openAndAsk(host, "如何创建采集工程？");

    await vi.waitFor(() => {
      expect(host.shadowRoot?.textContent).toContain("点击新建工程。");
      expect(host.shadowRoot?.textContent).toContain("采集工程");
      expect(host.shadowRoot?.textContent).toContain("资料 1");
      expect(host.shadowRoot?.textContent).not.toContain("helperFront/入门指南");
      expect(host.shadowRoot?.textContent).not.toContain(".md");
      expect(host.shadowRoot?.querySelector("a[href='/入门指南/2_从零搭建一个KF工程/2_数据采集配置']")).not.toBeNull();
      const thumb = host.shadowRoot?.querySelector("button.kiw-thumb img") as HTMLImageElement | null;
      expect(thumb?.src).toContain("/manuals/html/");
    });
  });

  it("restores the conversation from session storage after the widget is recreated", async () => {
    mockStream({ chunks: ["进入数采管理后点击新建。"], sources: [source] });

    const firstInstance = createKingIAskWidget(config);
    const firstHost = hostRoot();
    openAndAsk(firstHost, "如何创建采集工程？");

    await vi.waitFor(() => {
      expect(firstHost.shadowRoot?.textContent).toContain("进入数采管理后点击新建。");
    });

    firstInstance?.destroy();
    createKingIAskWidget(config);
    const secondHost = hostRoot();
    secondHost.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']")?.click();

    expect(secondHost.shadowRoot?.textContent).toContain("如何创建采集工程？");
    expect(secondHost.shadowRoot?.textContent).toContain("进入数采管理后点击新建。");
    expect(secondHost.shadowRoot?.querySelector("a[href='/入门指南/2_从零搭建一个KF工程/2_数据采集配置']")).not.toBeNull();
  });

  it("removes widget DOM when destroyed", () => {
    const instance = createKingIAskWidget(config);

    instance?.destroy();

    expect(document.querySelector("[data-kingiask-widget-root]")).toBeNull();
  });

  it("renders suggested questions and sends the question on click", async () => {
    const streamSpy = mockStream({ chunks: ["回答"], sources: [] });
    createKingIAskWidget({
      ...config,
      suggestedQuestions: ["如何创建采集工程？", "如何查看日志？"]
    });
    const host = hostRoot();
    host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']")?.click();

    const suggestions = host.shadowRoot?.querySelectorAll(".kiw-suggestion");
    expect(suggestions?.length).toBe(2);
    (suggestions?.[0] as HTMLButtonElement)?.click();

    await vi.waitFor(() => {
      expect(streamSpy).toHaveBeenCalledWith(
        expect.objectContaining({ apiBaseUrl: "http://rag.local:8000" }),
        "如何创建采集工程？",
        expect.anything(),
        expect.anything(),
        expect.anything(),
        expect.any(Object)
      );
      expect(host.shadowRoot?.textContent).toContain("回答");
    });
  });

  it("links [资料 N] in the answer to the corresponding source card", async () => {
    mockStream({ chunks: ["点击新建工程，详见[资料 1]。"], sources: [source] });
    createKingIAskWidget(config);
    const host = hostRoot();
    openAndAsk(host, "如何创建采集工程？");

    await vi.waitFor(() => {
      const anchor = host.shadowRoot?.querySelector("a.kiw-anchor") as HTMLAnchorElement | null;
      expect(anchor).not.toBeNull();
      expect(anchor?.getAttribute("href")).toBe("#kiw-source-1");
      expect(host.shadowRoot?.querySelector("#kiw-source-1")).not.toBeNull();
    });
  });

  it("clears the conversation when the clear button is clicked", async () => {
    mockStream({ chunks: ["回答内容"], sources: [] });
    createKingIAskWidget(config);
    const host = hostRoot();
    openAndAsk(host, "问题");

    await vi.waitFor(() => {
      expect(host.shadowRoot?.textContent).toContain("回答内容");
    });

    (host.shadowRoot?.querySelector(".kiw-clear") as HTMLButtonElement)?.click();

    expect(host.shadowRoot?.querySelectorAll(".kiw-message").length).toBe(1);
    expect(host.shadowRoot?.textContent).not.toContain("回答内容");
    expect(host.shadowRoot?.textContent).toContain("欢迎使用助手");
  });

  it("applies a custom accent color to the host", () => {
    createKingIAskWidget({ ...config, accentColor: "#ff6b00" });
    const host = hostRoot();
    expect(host.style.getPropertyValue("--kiw-accent")).toBe("#ff6b00");
  });

  it("renders image thumbnails and opens the lightbox on click", async () => {
    mockStream({ chunks: ["参考图片。"], sources: [source] });
    createKingIAskWidget(config);
    const host = hostRoot();
    openAndAsk(host, "图片");

    await vi.waitFor(() => {
      expect(host.shadowRoot?.querySelector("button.kiw-thumb")).not.toBeNull();
    });

    (host.shadowRoot?.querySelector("button.kiw-thumb") as HTMLButtonElement)?.click();
    const lightbox = host.shadowRoot?.querySelector(".kiw-lightbox");
    expect(lightbox?.classList.contains("open")).toBe(true);

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(lightbox?.classList.contains("open")).toBe(false);
    expect(host.shadowRoot?.querySelector("[data-role='panel']")?.classList.contains("open")).toBe(true);
  });

  it("shows an error bubble and removes the partial answer when streaming fails", async () => {
    vi.spyOn(api, "askKingIAskStream").mockRejectedValue(new Error("助手暂时不可用，请稍后再试。"));
    createKingIAskWidget(config);
    const host = hostRoot();
    openAndAsk(host, "问题");

    await vi.waitFor(() => {
      expect(host.shadowRoot?.querySelector(".kiw-error")?.textContent).toContain("助手暂时不可用");
    });
    // 半成品回答气泡已被移除，消息区只剩欢迎语 + 用户问题 + 错误。
    expect(host.shadowRoot?.querySelectorAll(".kiw-message").length).toBe(2);
  });
});
