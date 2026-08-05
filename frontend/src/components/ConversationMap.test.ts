import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { ChatMessage } from "../api/types";
import ConversationMap from "./ConversationMap.vue";

function message(id: string, role: "user" | "assistant", content: string): ChatMessage {
  return { id, role, content, sources: [], createdAt: "2026-01-01T00:00:00.000Z" };
}

const twoRounds: ChatMessage[] = [
  message("1", "user", "如何创建采集工程？"),
  message("2", "assistant", "点击新建工程，然后发布。"),
  message("3", "user", "那怎么运行？"),
  message("4", "assistant", "在工程列表选择并点击运行。"),
];

describe("ConversationMap", () => {
  it("少于两轮对话时不渲染导航条", () => {
    const wrapper = mount(ConversationMap, {
      props: {
        messages: [
          message("1", "user", "问题"),
          message("2", "assistant", "回答"),
        ],
      },
    });
    expect(wrapper.find('[data-testid="conversation-map"]').exists()).toBe(false);
  });

  it("每个方块代表一轮问答", () => {
    const wrapper = mount(ConversationMap, { props: { messages: twoRounds } });
    const dots = wrapper.findAll(".ka-map__dot");
    expect(dots.length).toBe(2);
  });

  it("hover 预览包含该轮问题与回答开头", () => {
    const wrapper = mount(ConversationMap, { props: { messages: twoRounds } });
    const firstTip = wrapper.findAll(".ka-map__tip")[0];
    expect(firstTip.text()).toContain("如何创建采集工程？");
    expect(firstTip.text()).toContain("点击新建工程");
  });

  it("点击方块发出对应用户消息下标", async () => {
    const wrapper = mount(ConversationMap, { props: { messages: twoRounds } });
    await wrapper.findAll(".ka-map__dot")[1].trigger("click");
    expect(wrapper.emitted("jump")?.[0]).toEqual([2]);
  });

  it("当前查看的轮次高亮放大", () => {
    const wrapper = mount(ConversationMap, {
      props: { messages: twoRounds, activeUserIndex: 2 },
    });
    const dots = wrapper.findAll(".ka-map__dot");
    expect(dots[0].classes()).not.toContain("is-active");
    expect(dots[1].classes()).toContain("is-active");
  });
});
