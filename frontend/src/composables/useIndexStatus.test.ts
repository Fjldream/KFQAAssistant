import { ref } from "vue";
import { describe, expect, it, vi } from "vitest";
import type { ApiSettings, IndexStatusResponse, ReadinessResponse } from "../api/types";
import { useIndexStatus } from "./useIndexStatus";

describe("useIndexStatus", () => {
  it("loads health, readiness, and index status", async () => {
    const readiness: ReadinessResponse = {
      status: "ready",
      checks: { index: "ok" },
      issues: [],
      chunks: 6291,
    };
    const indexStatus: IndexStatusResponse = {
      status: "ready",
      chunks: 6291,
      documents: 2275,
      last_built_at: "2026-07-29T09:00:00+00:00",
      index_signature: "same",
      current_signature: "same",
      config_matches: true,
      rebuild_pending: false,
      persist_dir: "storage/chroma",
      manifest_path: "storage/processed/index_manifest.json",
      issue: null,
    };
    const client = {
      health: vi.fn().mockResolvedValue({ status: "ok" }),
      readiness: vi.fn().mockResolvedValue(readiness),
      indexStatus: vi.fn().mockResolvedValue(indexStatus),
    };
    const settings = ref<ApiSettings>({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    const status = useIndexStatus(settings, client);

    await status.refresh();

    expect(status.health.value?.status).toBe("ok");
    expect(status.readiness.value?.chunks).toBe(6291);
    expect(status.indexStatus.value?.documents).toBe(2275);
    expect(status.errorMessage.value).toBeNull();
  });
});
