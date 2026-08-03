import { resolveConfig } from "./config";
import type { KingIAskWidgetApi, KingIAskWidgetConfig } from "./types";
import { createKingIAskWidget } from "./widget";

let currentInstance: { destroy: () => void } | null = null;
let automaticInitializationPending = document.readyState === "loading";

// 初始化小助手，重复初始化时先销毁旧实例，避免页面出现多个入口。
function init(config?: Partial<KingIAskWidgetConfig>): void {
  automaticInitializationPending = false;
  currentInstance?.destroy();
  const resolved = resolveConfig(config);
  currentInstance = createKingIAskWidget(resolved);
}

// 销毁小助手实例，供宿主页面在路由切换或关闭功能时调用。
function destroy(): void {
  automaticInitializationPending = false;
  currentInstance?.destroy();
  currentInstance = null;
}

const api: KingIAskWidgetApi = { init, destroy };

window.KingIAskWidget = api;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    if (automaticInitializationPending) {
      init();
    }
  }, { once: true });
} else {
  init();
}
