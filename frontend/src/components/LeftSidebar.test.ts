import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import LeftSidebar from "./LeftSidebar.vue";

describe("LeftSidebar", () => {
  it("emits ask when a common question is clicked", async () => {
    const wrapper = mount(LeftSidebar, {
      props: {
        healthLabel: "助手在线",
        indexLabel: "索引正常",
        documents: 2275,
        chunks: 6291,
        lastBuiltAt: "2026-07-29T09:00:00+00:00",
        commonQuestions: ["如何创建采集工程？"],
        recentQuestions: [],
      },
    });

    await wrapper.get("[data-testid='common-question']").trigger("click");

    expect(wrapper.emitted("ask")?.[0]).toEqual(["如何创建采集工程？"]);
  });

  it("renders recent questions inside a scrollable list container", () => {
    const wrapper = mount(LeftSidebar, {
      props: {
        healthLabel: "助手在线",
        indexLabel: "索引正常",
        documents: 2275,
        chunks: 6291,
        lastBuiltAt: "2026-07-29T09:00:00+00:00",
        commonQuestions: [],
        recentQuestions: Array.from({ length: 30 }, (_, index) => `最近问题 ${index + 1}`),
      },
    });

    expect(wrapper.get("[data-testid='recent-list']").classes()).toContain("ki-recent-list");
    expect(wrapper.findAll(".ki-recent-list .ki-question-button")).toHaveLength(30);
  });
});
