import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { SourceSnippet } from "../api/types";
import EvidencePanel from "./EvidencePanel.vue";

const sources: SourceSnippet[] = [
  {
    title: "资料A",
    source_path: "a.md",
    snippet: "这是命中的手册片段内容",
    evidence_ids: ["资料 1", "资料 2"],
    images: [],
    score: 0.86,
  },
];

describe("EvidencePanel", () => {
  it("空状态显示提示", () => {
    const wrapper = mount(EvidencePanel, { props: { sources: [], selectedSource: null } });
    expect(wrapper.text()).toContain("暂无资料");
  });

  it("渲染来源并显示相似度百分比", () => {
    const wrapper = mount(EvidencePanel, { props: { sources, selectedSource: null } });
    expect(wrapper.find('[data-testid="source-item"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("资料A");
    expect(wrapper.text()).toContain("86%");
  });

  it("当前选中来源高亮", () => {
    const wrapper = mount(EvidencePanel, { props: { sources, selectedSource: sources[0] } });
    expect(wrapper.find('[data-testid="source-item"]').classes()).toContain("is-active");
  });

  it("点击来源触发 openMaterial", async () => {
    const wrapper = mount(EvidencePanel, { props: { sources, selectedSource: null } });
    await wrapper.find('[data-testid="source-item"]').trigger("click");
    expect(wrapper.emitted("openMaterial")?.[0]).toEqual([sources[0]]);
  });

  it("点击收起按钮触发 collapse", async () => {
    const wrapper = mount(EvidencePanel, { props: { sources, selectedSource: null } });
    const collapseButton = wrapper.find(".ka-evidence__collapse");
    expect(collapseButton.exists()).toBe(true);
    await collapseButton.trigger("click");
    expect(wrapper.emitted("collapse")).toBeTruthy();
  });
});
