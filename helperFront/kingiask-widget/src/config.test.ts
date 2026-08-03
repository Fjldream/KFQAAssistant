import { describe, expect, it } from 'vitest';
import { DEFAULT_CONFIG, resolveConfig } from './config';

describe('resolveConfig', () => {
  it('keeps the widget disabled by default', () => {
    const config = resolveConfig();

    expect(config.enabled).toBe(false);
    expect(config.apiBaseUrl).toBe('');
    expect(config.title).toBe('KingIAsk');
    expect(config.position).toBe('right-bottom');
    expect(config.timeoutMs).toBe(60000);
    expect(config.persistSession).toBe(true);
  });

  it('merges global config and init overrides', () => {
    window.KINGIASK_WIDGET_CONFIG = {
      enabled: true,
      apiBaseUrl: 'http://example.local:8000/',
      title: '全局助手',
      apiKey: 'global-key',
    };

    const config = resolveConfig({
      title: '页面助手',
      timeoutMs: 15000,
      persistSession: false,
    });

    expect(config.enabled).toBe(true);
    expect(config.apiBaseUrl).toBe('http://example.local:8000');
    expect(config.title).toBe('页面助手');
    expect(config.apiKey).toBe('global-key');
    expect(config.timeoutMs).toBe(15000);
    expect(config.persistSession).toBe(false);

    delete window.KINGIASK_WIDGET_CONFIG;
  });

  it('uses a reusable default config object', () => {
    expect(DEFAULT_CONFIG.welcomeText).toContain('KF 产品手册');
  });
});
