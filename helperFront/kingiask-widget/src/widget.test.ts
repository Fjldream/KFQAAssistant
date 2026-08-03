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
  timeoutMs: 60000,
  persistSession: true
};

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

    const host = document.querySelector("[data-kingiask-widget-root]") as HTMLElement;
    const button = host.shadowRoot?.querySelector("button[data-role='launcher']") as HTMLButtonElement;
    button.click();

    expect(host.shadowRoot?.textContent).toContain("KingIAsk");
    expect(host.shadowRoot?.textContent).toContain("欢迎使用助手");
  });

  it("renders a branded launcher and dialog shell", () => {
    createKingIAskWidget(config);

    const host = document.querySelector("[data-kingiask-widget-root]") as HTMLElement;
    const launcher = host.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']");
    const panel = host.shadowRoot?.querySelector<HTMLElement>("[data-role='panel']");

    expect(launcher?.getAttribute("aria-label")).toBe("打开 KingIAsk 助手");
    expect(launcher?.textContent).toContain("KingIAsk");
    expect(panel?.getAttribute("role")).toBe("dialog");
    expect(panel?.getAttribute("aria-labelledby")).toBe("kiw-title");
  });

  it("sends a question and renders answer sources and images", async () => {
    vi.spyOn(api, "askKingIAsk").mockResolvedValue({
      answer: "点击新建工程。",
      sources: [
        {
          title: "采集工程",
          source_path: "helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置.md",
          snippet: "# helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置\n\n点击新建工程。",
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
      expect(host.shadowRoot?.textContent).toContain("资料 1");
      expect(host.shadowRoot?.textContent).not.toContain("helperFront/入门指南");
      expect(host.shadowRoot?.textContent).not.toContain(".md");
      expect(host.shadowRoot?.querySelector("a[href='/入门指南/2_从零搭建一个KF工程/2_数据采集配置']")).not.toBeNull();
      expect(host.shadowRoot?.querySelector("a[href='http://rag.local:8000/manuals/html/数采管理/1.png']")).not.toBeNull();
    });
  });

  it("restores the conversation from session storage after the widget is recreated", async () => {
    vi.spyOn(api, "askKingIAsk").mockResolvedValue({
      answer: "进入数采管理后点击新建。",
      sources: [
        {
          title: "数据采集配置",
          source_path: "helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置.md",
          snippet: "点击新建按钮创建采集工程。",
          evidence_ids: ["资料 1"],
          images: [],
          score: 0.9
        }
      ]
    });

    const firstInstance = createKingIAskWidget(config);
    const firstHost = document.querySelector("[data-kingiask-widget-root]") as HTMLElement;
    firstHost.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='launcher']")?.click();
    const textarea = firstHost.shadowRoot?.querySelector<HTMLTextAreaElement>("textarea[data-role='question']") as HTMLTextAreaElement;
    textarea.value = "如何创建采集工程？";
    firstHost.shadowRoot?.querySelector<HTMLButtonElement>("button[data-role='send']")?.click();

    await vi.waitFor(() => {
      expect(firstHost.shadowRoot?.textContent).toContain("进入数采管理后点击新建。");
    });

    firstInstance?.destroy();
    createKingIAskWidget(config);
    const secondHost = document.querySelector("[data-kingiask-widget-root]") as HTMLElement;
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
});
