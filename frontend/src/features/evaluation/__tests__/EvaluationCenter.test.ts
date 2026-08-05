import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import EvaluationCenter from "../EvaluationCenter.vue";
import EvaluationOverview from "../components/EvaluationOverview.vue";
import type { EvaluationApiClient } from "../api";
import type { EvaluationRunDetail, EvaluationRunSummary } from "../types";

function run(run_id: string, status: EvaluationRunSummary["status"]): EvaluationRunSummary {
  return {
    run_id,
    status,
    suite_id: "core",
    mode: "calibration",
    case_total: 1,
    case_passed: status === "completed" ? 1 : 0,
    pass_rate: status === "completed" ? 1 : 0,
    p0_total: 1,
    p0_passed: status === "completed" ? 1 : 0,
    p95_latency_ms: 120,
    avg_faithfulness_score: null,
  };
}

function detail(runId: string, status: EvaluationRunSummary["status"], passed = true): EvaluationRunDetail {
  return {
    summary: run(runId, status),
    gate_result: { passed, reasons: passed ? [] : ["P0 failed"] },
    case_results: [
      {
        case_id: "single.collect.create",
        category: "数采管理",
        priority: "P0",
        case_type: "single",
        passed,
        failure_reasons: passed ? [] : ["答案缺少关键步骤"],
        turn_results: [
          {
            question: "如何创建采集工程？",
            answer: "点击新建工程。",
            passed,
            faithfulness_score: null,
            faithfulness_claims: [],
            metric_results: [],
          },
        ],
        metric_results: [],
      },
    ],
  };
}

function createFakeClient(): EvaluationApiClient {
  return {
    listSuites: vi.fn().mockResolvedValue([{
      id: "core",
      version: "v1",
      cases: [{
        id: "single.collect.create",
        category: "数采管理",
        priority: "P0",
        case_type: "single",
        tags: [],
        turns: [{ question: "如何创建采集工程？" }],
      }],
    }]),
    listEvaluationRuns: vi.fn().mockResolvedValue([run("run-1", "completed")]),
    createRun: vi.fn().mockResolvedValue(run("run-2", "created")),
    getRun: vi.fn().mockResolvedValue(detail("run-1", "completed")),
    cancelRun: vi.fn().mockResolvedValue(run("run-2", "cancelled")),
    listBaselines: vi.fn().mockResolvedValue([{ suite_id: "core", run_id: "baseline-1", approved_by: "release", note: null, approved_at: "2026-08-05T00:00:00Z" }]),
    approveBaseline: vi.fn().mockResolvedValue({ suite_id: "core", run_id: "run-2", approved_by: "release", note: null, approved_at: "2026-08-05T00:00:00Z" }),
    compareRun: vi.fn().mockResolvedValue({ baseline_run_id: "baseline-1", pass_rate_delta: 0.1, recovered_case_ids: ["single.collect.create"] }),
  };
}

async function settle(): Promise<void> {
  await flushPromises();
}

afterEach(() => {
  vi.useRealTimers();
});

describe("EvaluationCenter", () => {
  it("creates a backend run and polls until completed", async () => {
    const client = createFakeClient();
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await settle();
    vi.useFakeTimers();
    client.getRun = vi.fn()
      .mockResolvedValueOnce(detail("run-2", "running"))
      .mockResolvedValueOnce(detail("run-2", "completed"));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await vi.advanceTimersByTimeAsync(2000);

    expect(client.createRun).toHaveBeenCalledWith({ suite_id: "core", mode: "calibration" });
    expect(wrapper.text()).toContain("COMPLETED");
    expect(wrapper.text()).toContain("未评估");
  });

  it("allows blocking mode only when the selected suite has an approved baseline", async () => {
    const noBaselineClient = createFakeClient();
    noBaselineClient.listBaselines = vi.fn().mockResolvedValue([]);
    const noBaselineWrapper = mount(EvaluationCenter, { props: { client: noBaselineClient } });
    await settle();

    await noBaselineWrapper.get('[data-testid="mode-blocking"]').trigger("click");
    expect(noBaselineWrapper.get('[data-testid="run-evaluation"]').attributes("disabled")).toBeDefined();

    const client = createFakeClient();
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await settle();
    await wrapper.get('[data-testid="mode-blocking"]').trigger("click");
    expect(wrapper.get('[data-testid="run-evaluation"]').attributes("disabled")).toBeUndefined();

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    expect(client.createRun).toHaveBeenCalledWith({ suite_id: "core", mode: "blocking" });
  });

  it("cancels an active backend run", async () => {
    const client = createFakeClient();
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await settle();
    client.createRun = vi.fn().mockResolvedValue(run("run-2", "running"));
    client.getRun = vi.fn().mockResolvedValue(detail("run-2", "running"));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await settle();
    await wrapper.get('[data-testid="abort-evaluation"]').trigger("click");
    await settle();

    expect(client.cancelRun).toHaveBeenCalledWith("run-2");
    expect(wrapper.text()).toContain("CANCELLED");
  });

  it("distinguishes invalid infrastructure results from failed quality gates", async () => {
    const client = createFakeClient();
    client.listEvaluationRuns = vi.fn().mockResolvedValue([run("run-invalid", "INVALID"), run("run-failed", "completed")]);
    client.getRun = vi.fn((id: string) => Promise.resolve(id === "run-invalid" ? detail(id, "INVALID") : detail(id, "completed", false)));
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await settle();

    expect(wrapper.text()).toContain("无效");
    await wrapper.findAll(".ke-row")[2].trigger("click");
    await settle();
    expect(wrapper.text()).toContain("质量未通过");
  });

  it("approves only a valid completed calibration run for the selected suite", async () => {
    const client = createFakeClient();
    client.getRun = vi.fn().mockResolvedValue(detail("run-1", "INVALID"));
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await settle();

    expect(wrapper.get('[data-testid="approve-baseline"]').attributes("disabled")).toBeDefined();
    client.getRun = vi.fn().mockResolvedValue(detail("run-1", "completed"));
    await wrapper.findAll(".ke-row")[1].trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="approve-baseline"]').attributes("disabled")).toBeUndefined();
    await wrapper.get('[data-testid="approve-baseline"]').trigger("click");
    await wrapper.get('[data-testid="approver-name"]').setValue("release manager");
    await wrapper.get("form").trigger("submit");
    await settle();

    expect(client.approveBaseline).toHaveBeenCalledWith("run-1", { approved_by: "release manager", note: undefined });
    expect(client.listBaselines).toHaveBeenCalledTimes(2);
    expect(client.compareRun).toHaveBeenCalledWith("run-1");
  });

  it("stops polling when unmounted", async () => {
    const client = createFakeClient();
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await settle();
    vi.useFakeTimers();
    client.createRun = vi.fn().mockResolvedValue(run("run-2", "created"));
    client.getRun = vi.fn().mockResolvedValue(detail("run-2", "running"));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await settle();
    wrapper.unmount();
    await vi.advanceTimersByTimeAsync(3000);

    expect(client.getRun).toHaveBeenCalledTimes(1);
  });

  it("continues polling when cancellation remains running until the backend reports cancelled", async () => {
    const client = createFakeClient();
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await settle();
    vi.useFakeTimers();
    client.createRun = vi.fn().mockResolvedValue(run("run-2", "running"));
    client.cancelRun = vi.fn().mockResolvedValue(run("run-2", "running"));
    client.getRun = vi.fn()
      .mockResolvedValueOnce(detail("run-2", "running"))
      .mockResolvedValueOnce(detail("run-2", "cancelled"));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await settle();
    await wrapper.get('[data-testid="abort-evaluation"]').trigger("click");
    await settle();

    expect(wrapper.find('[data-testid="abort-evaluation"]').exists()).toBe(true);
    await vi.advanceTimersByTimeAsync(1000);
    expect(client.getRun).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain("CANCELLED");
  });
});

describe("EvaluationOverview gate semantics", () => {
  it("renders a completed backend failed gate without calculating a new gate result", () => {
    const wrapper = mount(EvaluationOverview, { props: { detail: detail("run-failed", "completed", false) } });

    expect(wrapper.text()).toContain("质量未通过");
  });

  it("renders invalid semantics from the backend run status", () => {
    const wrapper = mount(EvaluationOverview, { props: { detail: detail("run-invalid", "INVALID", true) } });

    expect(wrapper.text()).toContain("无效");
  });
});
