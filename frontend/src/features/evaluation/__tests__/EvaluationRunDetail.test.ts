import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import EvaluationRunDetail from "../components/EvaluationRunDetail.vue";
import type { EvaluationRunDetail as Detail } from "../types";

function detail(): Detail {
  return {
    summary: {
      run_id: "run-diagnostic",
      status: "completed",
      case_total: 2,
      case_passed: 1,
      pass_rate: 0.5,
    },
    gate_result: { passed: false, reasons: ["P0 failed"] },
    case_results: [
      {
        case_id: "single.editor.enter",
        category: "页面编辑器",
        priority: "P0",
        case_type: "single",
        passed: false,
        failure_reasons: ["缺少答案关键词：页面管理"],
        metric_results: [],
        turn_results: [
          {
            question: "如何进入页面编辑器？",
            standalone_question: "如何进入页面编辑器？",
            answer: "手册中没有找到相关说明。",
            passed: false,
            faithfulness_score: null,
            faithfulness_claims: [],
            metric_results: [
              { name: "hit_at_k", score: 0, status: "FAILED", threshold: 1 },
            ],
            sources: [],
            missing_keywords: ["页面管理"],
            no_answer_passed: false,
            source_passed: false,
          },
        ],
      },
      {
        case_id: "single.collect.create",
        category: "数采管理",
        priority: "P0",
        case_type: "single",
        passed: true,
        failure_reasons: [],
        metric_results: [],
        turn_results: [
          {
            question: "如何创建采集工程？",
            answer: "点击新建工程，填写名称。[资料 1]",
            passed: true,
            faithfulness_score: 1,
            faithfulness_claims: [],
            metric_results: [
              { name: "faithfulness", score: 1, status: "PASSED", threshold: 0.9 },
            ],
            sources: [
              {
                title: "数采管理",
                source_path: "helperFront/数采管理.md",
                snippet: "进入数采管理模块，点击新建工程。",
                score: 0.89,
                images: ["step.png"],
              },
            ],
            matched_keywords: ["新建工程"],
            no_answer_passed: true,
            source_passed: true,
          },
        ],
      },
    ],
  };
}

describe("EvaluationRunDetail", () => {
  it("separates the question list from the selected diagnostic detail", async () => {
    const wrapper = mount(EvaluationRunDetail, { props: { detail: detail() } });

    expect(wrapper.get('[data-testid="evaluation-question-list"]').text()).toContain("如何进入页面编辑器？");
    expect(wrapper.get('[data-testid="selected-rag-answer"]').text()).toContain("手册中没有找到相关说明");

    await wrapper.findAll('[data-testid="evaluation-question-item"]')[1].trigger("click");

    expect(wrapper.get('[data-testid="selected-question"]').text()).toContain("如何创建采集工程？");
    expect(wrapper.get('[data-testid="selected-rag-answer"]').text()).toContain("点击新建工程");
    expect(wrapper.get('[data-testid="selected-sources"]').text()).toContain("helperFront/数采管理.md");
    expect(wrapper.get('[data-testid="selected-metrics"]').text()).toContain("faithfulness");
  });
});
