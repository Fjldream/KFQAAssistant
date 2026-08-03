import { computed, reactive } from "vue";
import type { ApiSettings } from "../api/types";

const SETTINGS_KEY = "kingiask.settings";

const defaultSettings: ApiSettings = {
  apiBaseUrl: "http://127.0.0.1:8000",
  apiKey: "",
};

// 从 localStorage 读取前端配置，读取失败时回退到默认值。
function loadSettings(): ApiSettings {
  const raw = window.localStorage.getItem(SETTINGS_KEY);
  if (!raw) {
    return { ...defaultSettings };
  }
  try {
    return { ...defaultSettings, ...(JSON.parse(raw) as Partial<ApiSettings>) };
  } catch {
    return { ...defaultSettings };
  }
}

// 保存前端配置到 localStorage，让刷新页面后仍然能复用 API 地址和密钥。
function saveSettings(settings: ApiSettings): void {
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

const state = reactive<ApiSettings>(loadSettings());

// 管理 KingIAsk 的本地 API 配置，并暴露保存和重置能力。
export function useSettings() {
  const settings = computed<ApiSettings>(() => ({
    apiBaseUrl: state.apiBaseUrl,
    apiKey: state.apiKey,
  }));

  function updateSettings(next: ApiSettings): void {
    state.apiBaseUrl = next.apiBaseUrl;
    state.apiKey = next.apiKey;
    saveSettings(state);
  }

  function resetSettings(): void {
    state.apiBaseUrl = defaultSettings.apiBaseUrl;
    state.apiKey = defaultSettings.apiKey;
    saveSettings(state);
  }

  return {
    settings,
    updateSettings,
    resetSettings,
  };
}
