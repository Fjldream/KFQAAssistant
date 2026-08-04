import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import type { ChatMessage } from "../api/types";
import ChatWorkspace from "./ChatWorkspace.vue";

const commonQuestions = ["如何创建采集工程？", "客户端支持哪些系统？"];

describe("ChatWorkspace", () => {
  it("空会话显示欢迎态和 starter", () => {
    const wrapper = mount(ChatWorkspace, {
      props: { messages: [], isAsking: false, errorMessage: null, commonQuestions },
    });
    expect(wrapper.find(".ka-welcome").exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="welcome-starter"]').length).toBe(2);
  });

  it("点击 starter 触发 ask 事件", async () => {
    const wrapper = mount(ChatWorkspace, {
      props: { messages: [], isAsking: false, errorMessage: null, commonQuestions },
    });
    await wrapper.find('[data-testid="welcome-starter"]').trigger("click");
    expect(wrapper.emitted("ask")?.[0]).toEqual(["如何创建采集工程？"]);
  });

  it("输入问题提交后触发 ask 并清空输入框", async () => {
    const wrapper = mount(ChatWorkspace, {
      props: { messages: [], isAsking: false, errorMessage: null, commonQuestions: [] },
    });
    await wrapper.find("textarea").setValue("页面编辑器主要包括哪些区域？");
    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("ask")?.[0]).toEqual(["页面编辑器主要包括哪些区域？"]);
    expect((wrapper.find("textarea").element as HTMLTextAreaElement).value).toBe("");
  });

  it("Enter 键发送、Shift+Enter 不发送", async () => {
    const wrapper = mount(ChatWorkspace, {
      props: { messages: [], isAsking: false, errorMessage: null, commonQuestions: [] },
    });
    const textarea = wrapper.find("textarea");
    await textarea.setValue("问题");
    await textarea.trigger("keydown.enter", { shiftKey: true });
    expect(wrapper.emitted("ask")).toBeUndefined();
    await textarea.trigger("keydown.enter");
    expect(wrapper.emitted("ask")?.[0]).toEqual(["问题"]);
  });

  it("渲染用户与助手消息，助手消息显示来源 chip", () => {
    const messages: ChatMessage[] = [
      {
        id: "1",
        role: "user",
        content: "你好",
        sources: [],
        createdAt: "2026-01-01T00:00:00.000Z",
      },
      {
        id: "2",
        role: "assistant",
        content: "**回答内容**",
        sources: [
          {
            title: "资料A",
            source_path: "a.md",
            snippet: "片段",
            evidence_ids: ["资料 1"],
            images: [],
            score: 0.8,
          },
        ],
        createdAt: "2026-01-01T00:00:01.000Z",
      },
    ];
    const wrapper = mount(ChatWorkspace, {
      props: { messages, isAsking: false, errorMessage: null, commonQuestions: [] },
    });
    expect(wrapper.findAll(".ka-msg").length).toBe(2);
    expect(wrapper.findAll(".ka-msg__bubble")[1].html()).toContain("<strong>回答内容</strong>");
    expect(wrapper.find(".ka-source-chip").text()).toContain("资料 1");
  });

  it("流式进行中的助手消息显示打字光标而非 Markdown", () => {
    const streamingMessages: ChatMessage[] = [
      {
        id: "1",
        role: "user",
        content: "问题",
        sources: [],
        createdAt: "2026-01-01T00:00:00.000Z",
      },
      {
        id: "2",
        role: "assistant",
        content: "正在生成**回答**",
        sources: [],
        createdAt: "2026-01-01T00:00:01.000Z",
        streaming: true,
      },
    ];
    const wrapper = mount(ChatWorkspace, {
      props: { messages: streamingMessages, isAsking: true, errorMessage: null, commonQuestions: [] },
    });
    // 流式期间按纯文本展示（不渲染 <strong>），并出现打字光标。
    expect(wrapper.findAll(".ka-msg__bubble")[1].html()).toContain("正在生成**回答**");
    expect(wrapper.find(".ka-stream-cursor").exists()).toBe(true);
    // 已有流式占位消息时不再叠加"正在思考"气泡。
    expect(wrapper.findAll(".ka-msg").length).toBe(2);
  });

  it("清空按钮触发 clear 事件", async () => {
    const wrapper = mount(ChatWorkspace, {
      props: { messages: [], isAsking: false, errorMessage: null, commonQuestions: [] },
    });
    const clearButton = wrapper
      .findAll("button")
      .find((b) => b.text().includes("清空会话"));
    expect(clearButton).toBeDefined();
    await clearButton!.trigger("click");
    expect(wrapper.emitted("clear")).toBeTruthy();
  });

  it("错误信息展示在输入栏上方", () => {
    const wrapper = mount(ChatWorkspace, {
      props: { messages: [], isAsking: false, errorMessage: "后端未连接", commonQuestions: [] },
    });
    expect(wrapper.find(".ka-error").text()).toContain("后端未连接");
  });
});
