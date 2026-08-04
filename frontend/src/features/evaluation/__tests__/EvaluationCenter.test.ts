import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import EvaluationCenter from "../EvaluationCenter.vue";
import type { EvaluationApiClient } from "../api";

function createFakeClient(): EvaluationApiClient {
  return {
    listEvaluationCases: vi.fn().mockResolvedValue([
      {
        id: "single.collect.create",
        category: "数采管理",
        priority: "P0",
        case_type: "single",
        tags: ["smoke"],
        turns: [{ question: "如何创建采集工程？", expected_keywords: ["新建工程"] }],
      },
    ]),
    getEvaluationOverview: vi.fn().mockResolvedValue({
      latest: {
        summary: {
          run_id: "run-1",
          status: "completed",
          case_total: 1,
          case_passed: 1,
          pass_rate: 1,
          p0_total: 1,
          p0_passed: 1,
          avg_latency_ms: 120,
          p95_latency_ms: 120,
        },
        gate_result: { passed: true, reasons: [] },
        case_results: [
          {
            case_id: "single.collect.create",
            category: "数采管理",
            priority: "P0",
            case_type: "single",
            passed: true,
            turn_results: [{ question: "如何创建采集工程？", answer: "点击新建工程。", passed: true }],
            failure_reasons: [],
            elapsed_ms: 120,
          },
        ],
      },
      previous_run_id: null,
      comparison: null,
    }),
    listEvaluationRuns: vi.fn().mockResolvedValue([
      {
        run_id: "run-1",
        status: "completed",
        case_total: 1,
        case_passed: 1,
        pass_rate: 1,
      },
    ]),
    createEvaluationRun: vi.fn().mockResolvedValue({
      summary: { run_id: "run-2", status: "completed", case_total: 1, case_passed: 1, pass_rate: 1 },
      gate_result: { passed: true, reasons: [] },
      case_results: [],
    }),
    runEvaluationCase: vi.fn().mockResolvedValue({
      case_id: "single.collect.create",
      category: "数采管理",
      priority: "P0",
      case_type: "single",
      passed: true,
      turn_results: [{ question: "如何创建采集工程？", answer: "点击新建工程。", passed: true }],
      failure_reasons: [],
      elapsed_ms: 120,
    }),
    saveProgressiveRun: vi.fn().mockResolvedValue({
      summary: { run_id: "run-2", status: "completed", case_total: 1, case_passed: 1, pass_rate: 1 },
      gate_result: { passed: true, reasons: [] },
      case_results: [],
    }),
    getEvaluationRun: vi.fn().mockResolvedValue({
      summary: { run_id: "run-1", status: "completed", case_total: 1, case_passed: 1, pass_rate: 1 },
      gate_result: { passed: true, reasons: [] },
      case_results: [],
    }),
    compareEvaluationRun: vi.fn().mockResolvedValue({ pass_rate_delta: 0 }),
  };
}

describe("EvaluationCenter", () => {
  it("展示评测总览、用例列表和运行入口", async () => {
    const client = createFakeClient();
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("评测中心");
    expect(wrapper.text()).toContain("通过率");
    expect(wrapper.text()).toContain("single.collect.create");
    expect(wrapper.text()).toContain("运行评测");
  });

  it("点击运行评测会调用 API 并展示新报告", async () => {
    const client = createFakeClient();
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await new Promise((resolve) => setTimeout(resolve, 0));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(client.runEvaluationCase).toHaveBeenCalledWith("single.collect.create", { include_dialogues: true }, expect.anything());
    expect(client.saveProgressiveRun).toHaveBeenCalled();
    expect(wrapper.text()).toContain("run-2");
  });

  it("运行评测期间展示状态提示", async () => {
    const client = createFakeClient();
    let resolveRun: (value: unknown) => void = () => {};
    client.runEvaluationCase = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveRun = resolve;
        }),
    ) as EvaluationApiClient["runEvaluationCase"];
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await new Promise((resolve) => setTimeout(resolve, 0));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("正在运行评测");
    expect(wrapper.text()).toContain("运行中");
    resolveRun({
      case_id: "single.collect.create",
      category: "数采管理",
      priority: "P0",
      case_type: "single",
      passed: true,
      turn_results: [],
    });
  });

  it("运行失败时展示后端错误", async () => {
    const client = createFakeClient();
    client.runEvaluationCase = vi.fn().mockRejectedValue(new Error("大模型服务暂时不可用，请稍后重试。"));
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await new Promise((resolve) => setTimeout(resolve, 0));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("大模型服务暂时不可用，请稍后重试。");
    expect(wrapper.text()).toContain("接口错误");
  });

  it("可以中止评测并停止后续保存", async () => {
    const client = createFakeClient();
    let rejectRun: (reason: unknown) => void = () => {};
    client.runEvaluationCase = vi.fn(
      () =>
        new Promise((_resolve, reject) => {
          rejectRun = reject;
        }),
    ) as EvaluationApiClient["runEvaluationCase"];
    const wrapper = mount(EvaluationCenter, { props: { client } });
    await new Promise((resolve) => setTimeout(resolve, 0));

    await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
    await new Promise((resolve) => setTimeout(resolve, 0));
    await wrapper.get('[data-testid="abort-evaluation"]').trigger("click");
    rejectRun(new DOMException("Aborted", "AbortError"));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("已中止");
    expect(client.saveProgressiveRun).not.toHaveBeenCalled();
  });
});
