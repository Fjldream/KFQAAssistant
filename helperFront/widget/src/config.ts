import type {
  KingIAskWidgetConfig,
  ResolvedKingIAskWidgetConfig,
} from './types';

export const DEFAULT_CONFIG: ResolvedKingIAskWidgetConfig = {
  enabled: false,
  apiBaseUrl: '',
  apiKey: '',
  title: 'KingIAsk',
  welcomeText: '你好，我可以帮你查询 KF 产品手册。',
  position: 'right-bottom',
  timeoutMs: 60000,
};

// 合并默认配置、全局配置和 init 入参，得到插件运行时使用的最终配置。
export function resolveConfig(
  overrides: Partial<KingIAskWidgetConfig> = {},
): ResolvedKingIAskWidgetConfig {
  const merged = {
    ...DEFAULT_CONFIG,
    ...(window.KINGIASK_WIDGET_CONFIG ?? {}),
    ...overrides,
  };
  return {
    ...merged,
    apiBaseUrl: String(merged.apiBaseUrl ?? '').replace(/\/+$/, ''),
    apiKey: String(merged.apiKey ?? ''),
    title: String(merged.title ?? DEFAULT_CONFIG.title),
    welcomeText: String(merged.welcomeText ?? DEFAULT_CONFIG.welcomeText),
    position:
      merged.position === 'left-bottom' ? 'left-bottom' : 'right-bottom',
    timeoutMs: Number(merged.timeoutMs || DEFAULT_CONFIG.timeoutMs),
  };
}
