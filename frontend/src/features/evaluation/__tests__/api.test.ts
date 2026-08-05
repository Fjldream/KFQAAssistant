import { afterEach, describe, expect, it, vi } from "vitest";
import { createEvaluationApiClient } from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createEvaluationApiClient", () => {
  it("creates a trusted calibration run without browser case results", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ run_id: "run-1" }) });
    vi.stubGlobal("fetch", fetchMock);

    const client = createEvaluationApiClient({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    await client.createRun({ suite_id: "core", mode: "calibration" });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8000/api/evaluation/runs");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ suite_id: "core", mode: "calibration" }));
    expect(fetchMock.mock.calls.map(([requestUrl]) => requestUrl)).not.toContain(
      "http://127.0.0.1:8000/api/evaluation/runs/progressive",
    );
  });

  it("cancels and approves a trusted run through lifecycle endpoints", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    const client = createEvaluationApiClient({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    await client.cancelRun("run/1");
    await client.approveBaseline("run/1", { approved_by: "release manager", note: "known good" });

    expect(fetchMock.mock.calls[0][0]).toBe("http://127.0.0.1:8000/api/evaluation/runs/run%2F1/cancel");
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: "POST" });
    expect(fetchMock.mock.calls[1][0]).toBe("http://127.0.0.1:8000/api/evaluation/runs/run%2F1/approve-baseline");
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({ approved_by: "release manager", note: "known good" }),
    });
  });

  it("loads trusted run detail, approvals, and approved-baseline comparison", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    const client = createEvaluationApiClient({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "secret" });
    await client.getRun("run-1");
    await client.listBaselines();
    await client.compareRun("run-1");

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "http://127.0.0.1:8000/api/evaluation/runs/run-1",
      "http://127.0.0.1:8000/api/evaluation/baselines",
      "http://127.0.0.1:8000/api/evaluation/runs/run-1/compare",
    ]);
  });
});
