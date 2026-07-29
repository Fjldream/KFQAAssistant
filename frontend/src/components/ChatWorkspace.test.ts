import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { ChatMessage } from "../api/types";
import ChatWorkspace from "./ChatWorkspace.vue";

describe("ChatWorkspace", () => {
  it("emits ask when Enter is pressed in the question input", async () => {
    const wrapper = mount(ChatWorkspace, {
      props: {
        messages: [],
        isAsking: false,
        errorMessage: null,
      },
    });

    const input = wrapper.get("textarea");
    await input.setValue("如何创建采集工程？");
    await input.trigger("keydown", { key: "Enter" });

    expect(wrapper.emitted("ask")?.[0]).toEqual(["如何创建采集工程？"]);
  });

  it("renders assistant markdown and source chips", () => {
    const messages: ChatMessage[] = [
      {
        id: "assistant-1",
        role: "assistant",
        content: "**步骤**：点击新建工程。",
        createdAt: "2026-07-29T09:00:00+00:00",
        sources: [
          {
            title: "工程开发-Windows",
            source_path: "html/数采管理/工程开发-Windows/index.html",
            snippet: "点击新建工程按钮。",
            evidence_ids: ["资料 1"],
            images: [],
            score: 0.82,
          },
        ],
      },
    ];

    const wrapper = mount(ChatWorkspace, {
      props: {
        messages,
        isAsking: false,
        errorMessage: null,
      },
    });

    expect(wrapper.html()).toContain("<strong>步骤</strong>");
    expect(wrapper.text()).toContain("工程开发-Windows");
  });

  it("renders a thinking indicator while asking", () => {
    const wrapper = mount(ChatWorkspace, {
      props: {
        messages: [],
        isAsking: true,
        errorMessage: null,
      },
    });

    expect(wrapper.find(".ki-thinking-message").exists()).toBe(true);
    expect(wrapper.text()).toContain("正在检索手册");
    expect(wrapper.text()).toContain("组织回答");
  });
});
