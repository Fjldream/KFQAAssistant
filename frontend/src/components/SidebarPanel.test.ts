import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { ChatSession } from "../api/types";
import SidebarPanel from "./SidebarPanel.vue";

const sessions: ChatSession[] = [
  {
    id: "a",
    title: "会话A",
    createdAt: "2026-01-01T00:00:00.000Z",
    updatedAt: "2026-01-01T00:00:00.000Z",
    conversationSummary: "",
    messages: [],
  },
  {
    id: "b",
    title: "会话B",
    createdAt: "2026-01-01T00:00:00.000Z",
    updatedAt: "2026-01-01T00:00:00.000Z",
    conversationSummary: "",
    messages: [],
  },
];

const baseProps = {
  healthLabel: "助手在线",
  healthState: "ok" as const,
  indexLabel: "索引正常",
  indexState: "ok" as const,
  documents: 12,
  chunks: 120,
  lastBuiltAt: "2026-01-01T00:00:00.000Z",
  commonQuestions: ["如何创建采集工程？"],
  recentQuestions: ["最近问题1"],
  sessions,
  activeSessionId: "a",
};

describe("SidebarPanel", () => {
  it("渲染状态、会话、常用问题和最近提问", () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    expect(wrapper.text()).toContain("助手在线");
    expect(wrapper.text()).toContain("会话A");
    expect(wrapper.text()).toContain("会话B");
    expect(wrapper.text()).toContain("如何创建采集工程？");
    expect(wrapper.text()).toContain("最近问题1");
  });

  it("当前会话高亮", () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    const items = wrapper.findAll(".ka-session");
    expect(items[0].classes()).toContain("is-active");
    expect(items[1].classes()).not.toContain("is-active");
  });

  it("点击会话项触发 switchSession", async () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    await wrapper.findAll('[data-testid="session-item"]')[1].trigger("click");
    expect(wrapper.emitted("switchSession")?.[0]).toEqual(["b"]);
  });

  it("点击删除按钮触发 deleteSession 且不触发 switchSession", async () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    const deleteButton = wrapper.find(".ka-session__del");
    await deleteButton.trigger("click");
    expect(wrapper.emitted("deleteSession")?.[0]).toEqual(["a"]);
    expect(wrapper.emitted("switchSession")).toBeUndefined();
  });

  it("新建按钮触发 newSession", async () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    const newButton = wrapper
      .findAll("button")
      .find((b) => b.text().includes("新建"));
    expect(newButton).toBeDefined();
    await newButton!.trigger("click");
    expect(wrapper.emitted("newSession")).toBeTruthy();
  });

  it("点击常用问题触发 ask", async () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    await wrapper.find('[data-testid="common-question"]').trigger("click");
    expect(wrapper.emitted("ask")?.[0]).toEqual(["如何创建采集工程？"]);
  });

  it("点击设置按钮触发 openSettings", async () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    const settingsButton = wrapper
      .findAll("button")
      .find((b) => b.attributes("title") === "设置");
    expect(settingsButton).toBeDefined();
    await settingsButton!.trigger("click");
    expect(wrapper.emitted("openSettings")).toBeTruthy();
  });

  it("清空最近提问触发 clearHistory", async () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    const clearButton = wrapper
      .findAll("button")
      .find((b) => b.text().includes("清空"));
    expect(clearButton).toBeDefined();
    await clearButton!.trigger("click");
    expect(wrapper.emitted("clearHistory")).toBeTruthy();
  });

  it("点击删除按钮移除单条最近提问，且不触发 ask", async () => {
    const wrapper = mount(SidebarPanel, { props: baseProps });
    const removeButtons = wrapper.findAll('[data-testid="remove-recent"]');
    expect(removeButtons.length).toBe(1);
    await removeButtons[0].trigger("click");
    expect(wrapper.emitted("removeRecentQuestion")?.[0]).toEqual(["最近问题1"]);
    expect(wrapper.emitted("ask")).toBeUndefined();
  });

  it("过长的文本带 title 悬浮提示", () => {
    const longQuestion = "这是一段非常非常长的最近提问，用来验证省略号与悬浮提示的完整内容展示效果";
    const wrapper = mount(SidebarPanel, {
      props: { ...baseProps, recentQuestions: [longQuestion], commonQuestions: [longQuestion] },
    });
    const recentText = wrapper.find('[data-testid="recent-list"] .ka-list-item__text');
    expect(recentText.attributes("title")).toBe(longQuestion);
    const commonText = wrapper.find('[data-testid="common-question"] .ka-list-item__text');
    expect(commonText.attributes("title")).toBe(longQuestion);
  });
});
