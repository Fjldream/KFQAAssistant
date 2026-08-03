import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useTheme } from "./useTheme";

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useTheme", () => {
  it("默认偏好为跟随系统", () => {
    const theme = useTheme();
    expect(theme.preference.value).toBe("system");
  });

  it("设置深色后应用到 html 并持久化", () => {
    const theme = useTheme();
    theme.setPreference("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage.getItem("kingiask-deep.theme")).toBe("dark");
  });

  it("设置浅色后应用到 html", () => {
    const theme = useTheme();
    theme.setPreference("light");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("system 模式跟随系统深色偏好", () => {
    vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true, addEventListener: vi.fn() }));
    const theme = useTheme();
    theme.setPreference("system");
    expect(theme.resolvedTheme.value).toBe("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
