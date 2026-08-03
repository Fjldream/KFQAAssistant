import { beforeEach, describe, expect, it } from "vitest";
import { useSettings } from "./useSettings";

describe("useSettings", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("persists API settings locally", () => {
    const { settings, updateSettings } = useSettings();

    updateSettings({ apiBaseUrl: "http://localhost:8000", apiKey: "test-key" });

    expect(settings.value.apiBaseUrl).toBe("http://localhost:8000");
    expect(JSON.parse(window.localStorage.getItem("kingiask.settings") ?? "{}")).toEqual({
      apiBaseUrl: "http://localhost:8000",
      apiKey: "test-key",
    });
  });
});
