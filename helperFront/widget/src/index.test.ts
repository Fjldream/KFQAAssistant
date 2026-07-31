import { afterEach, describe, expect, it, vi } from "vitest";

const readyStateDescriptor = Object.getOwnPropertyDescriptor(document, "readyState");

function setReadyState(value: DocumentReadyState): void {
  Object.defineProperty(document, "readyState", {
    configurable: true,
    value
  });
}

function root(): HTMLElement | null {
  return document.querySelector("[data-kingiask-widget-root]");
}

async function loadEntry(): Promise<void> {
  await import("./index");
}

describe("KingIAskWidget global API", () => {
  afterEach(() => {
    window.KingIAskWidget?.destroy();
    document.body.replaceChildren();
    delete window.KINGIASK_WIDGET_CONFIG;
    delete window.KingIAskWidget;
    if (readyStateDescriptor) {
      Object.defineProperty(document, "readyState", readyStateDescriptor);
    } else {
      delete (document as { readyState?: DocumentReadyState }).readyState;
    }
    vi.resetModules();
  });

  it("automatically initializes after DOM content loads", async () => {
    setReadyState("loading");
    window.KINGIASK_WIDGET_CONFIG = { enabled: true, title: "自动助手" };

    await loadEntry();
    expect(root()).toBeNull();

    document.dispatchEvent(new Event("DOMContentLoaded"));

    expect(root()?.shadowRoot?.textContent).toContain("自动助手");
  });

  it("replaces the previous root when initialized repeatedly", async () => {
    setReadyState("complete");
    await loadEntry();

    window.KingIAskWidget?.init({ enabled: true, title: "第一次初始化" });
    window.KingIAskWidget?.init({ enabled: true, title: "第二次初始化" });

    expect(document.querySelectorAll("[data-kingiask-widget-root]")).toHaveLength(1);
    expect(root()?.shadowRoot?.textContent).toContain("第二次初始化");
  });

  it("does not render UI when initialized as disabled", async () => {
    setReadyState("complete");
    await loadEntry();

    window.KingIAskWidget?.init({ enabled: false });

    expect(root()).toBeNull();
  });

  it("removes the root when destroyed", async () => {
    setReadyState("complete");
    await loadEntry();
    window.KingIAskWidget?.init({ enabled: true });

    window.KingIAskWidget?.destroy();

    expect(root()).toBeNull();
  });

  it("does not auto-initialize after destroy before DOM content loads", async () => {
    setReadyState("loading");
    window.KINGIASK_WIDGET_CONFIG = { enabled: true };
    await loadEntry();

    window.KingIAskWidget?.destroy();
    document.dispatchEvent(new Event("DOMContentLoaded"));

    expect(root()).toBeNull();
  });

  it("preserves an explicit early init configuration after DOM content loads", async () => {
    setReadyState("loading");
    window.KINGIASK_WIDGET_CONFIG = { enabled: true, title: "自动配置" };
    await loadEntry();

    window.KingIAskWidget?.init({ enabled: true, title: "自定义配置" });
    document.dispatchEvent(new Event("DOMContentLoaded"));

    expect(document.querySelectorAll("[data-kingiask-widget-root]")).toHaveLength(1);
    expect(root()?.shadowRoot?.textContent).toContain("自定义配置");
  });
});
