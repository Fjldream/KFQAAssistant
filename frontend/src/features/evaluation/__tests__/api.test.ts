import { afterEach, describe, expect, it, vi } from "vitest";
import { createEvaluationApiClient } from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createEvaluationApiClient", () => {
  it("请求评测用例列表", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    vi.stubGlobal("fetch", fetchMock);

    const client = createEvaluationApiClient({ apiBaseUrl: "http://127.0.0.1:8000/", apiKey: "secret" });
    await client.listEvaluationCases();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8000/api/evaluation/cases");
    expect(new Headers(init.headers).get("X-API-Key")).toBe("secret");
  });

  it("创建评测运行", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ summary: { run_id: "run-1" } }) });
    vi.stubGlobal("fetch", fetchMock);

    const client = createEvaluationApiClient({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    await client.createEvaluationRun({ include_dialogues: true, include_load_test: false });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8000/api/evaluation/runs");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ include_dialogues: true, include_load_test: false }));
  });

  it("运行单条评测用例并保存渐进式运行", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    const client = createEvaluationApiClient({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    await client.runEvaluationCase("case/1", { include_dialogues: true });
    await client.saveProgressiveRun({ case_results: [], config: { mode: "progressive" } });

    expect(fetchMock.mock.calls[0][0]).toBe("http://127.0.0.1:8000/api/evaluation/cases/case%2F1/run");
    expect(fetchMock.mock.calls[1][0]).toBe("http://127.0.0.1:8000/api/evaluation/runs/progressive");
  });

  it("请求评测运行详情和对比结果", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    const client = createEvaluationApiClient({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    await client.getEvaluationRun("run-1");
    await client.compareEvaluationRun("run-1", "run-0");

    expect(fetchMock.mock.calls[0][0]).toBe("http://127.0.0.1:8000/api/evaluation/runs/run-1");
    expect(fetchMock.mock.calls[1][0]).toBe(
      "http://127.0.0.1:8000/api/evaluation/runs/run-1/compare?baseline_run_id=run-0",
    );
  });
});
