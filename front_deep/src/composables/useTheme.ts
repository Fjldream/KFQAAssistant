import { computed, ref } from "vue";
import type { ThemePreference } from "../api/types";

const THEME_KEY = "kingiask-deep.theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

// 从 localStorage 读取主题偏好，默认跟随系统。
function loadPreference(): ThemePreference {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(THEME_KEY);
  } catch {
    return "system";
  }
  if (raw === "light" || raw === "dark" || raw === "system") {
    return raw;
  }
  return "system";
}

function persistPreference(preference: ThemePreference): void {
  try {
    window.localStorage.setItem(THEME_KEY, preference);
  } catch {
    // 存储不可用时静默失败，主题仍在当前会话生效。
  }
}

// 解析偏好为实际主题，并把结果写到 <html data-theme> 供 CSS 消费。
function resolveTheme(preference: ThemePreference): "light" | "dark" {
  if (preference !== "system") {
    return preference;
  }
  return window.matchMedia?.(DARK_QUERY)?.matches ? "dark" : "light";
}

function applyTheme(resolved: "light" | "dark"): void {
  document.documentElement.dataset.theme = resolved;
}

const preference = ref<ThemePreference>(loadPreference());

// 初始化时立即应用一次主题，避免页面闪烁。
applyTheme(resolveTheme(preference.value));

// 跟随系统：系统深浅色变化时自动刷新 resolved 主题。
window.matchMedia?.(DARK_QUERY)?.addEventListener?.("change", (event) => {
  if (preference.value === "system") {
    applyTheme(event.matches ? "dark" : "light");
  }
});

// 管理浅色 / 深色 / 跟随系统三态主题，持久化到 localStorage。
export function useTheme() {
  const resolvedTheme = computed<"light" | "dark">(() => resolveTheme(preference.value));

  function setPreference(next: ThemePreference): void {
    preference.value = next;
    persistPreference(next);
    applyTheme(resolveTheme(next));
  }

  return {
    preference,
    resolvedTheme,
    setPreference,
  };
}
