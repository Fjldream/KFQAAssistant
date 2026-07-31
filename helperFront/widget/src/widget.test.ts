import { afterEach, describe, expect, it, vi } from "vitest";
import type { ResolvedKingIAskWidgetConfig } from "./types";
import { createKingIAskWidget } from "./widget";
import * as api from "./api";

const config: ResolvedKingIAskWidgetConfig = {
  enabled: true,
  apiBaseUrl: "http://rag.local:8000",
  apiKey: "",
  title: "KingIAsk",
  welcomeText: "欢迎使用助手",
  position: "right-bottom",
  timeoutMs: 60000
};

describe("createKingIAskWidget", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
  });

  it("does not render when disabled", () => {
    const instance = createKingIAskWidget({ ...config, enabled: false });

    expect(instance).toBeNull();
    expect(document.querySelector("[data-kingiask-widget-root]")).toBeNull();
  });

  it("renders a floating button and opens the panel", () => {
    createKingIAskWidget(config);

    const host = document.querySelector("[data-kingiask-widget-root]") as HTMLElement;
    const button = host.shadowRoot?.querySelector("button[data-role='launcher']") as HTMLButtonElement;
    button.click();

    expect(host.shadowRoot?.textContent).toContain("KingIAsk");
    expect(host.shadowRoot?.textContent).toContain("欢迎使用助手");
  });

  it("sends a question and renders answer sources and images", async () => {
    vi.spyOn(api, "askKingIAsk").mockResolvedValue({
      answer: "点击新建工程。",
      sources: [
        {
          title: "采集工程",
          source_path: "html/数采管理/工程开发-Windows.md",
          snippet: "点击新建工程。",
          evidence_ids: ["资料 1"],
          images: ["html/数采管理/1.png"],
          score: 0.9
        }
      ]
    });

    createKingIAskWidget(config);
    const host = document.querySelector("[data-kingiask-widget-root]") as HTMLElement;
    host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']")?.click();
    const textarea = host.shadowRoot?.querySelector<HTMLTextAreaElement>("textarea[data-role='question']") as HTMLTextAreaElement;
    textarea.value = "如何创建采集工程？";
    textarea.dispatchEvent(new Event("input"));
    host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='send']")?.click();

    await vi.waitFor(() => {
      expect(host.shadowRoot?.textContent).toContain("点击新建工程。");
      expect(host.shadowRoot?.textContent).toContain("采集工程");
      expect(host.shadowRoot?.querySelector("a[href='http://rag.local:8000/manuals/html/数采管理/1.png']")).not.toBeNull();
    });
  });

  it("removes widget DOM when destroyed", () => {
    const instance = createKingIAskWidget(config);

    instance?.destroy();

    expect(document.querySelector("[data-kingiask-widget-root]")).toBeNull();
  });
});
