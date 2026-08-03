import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick, ref } from "vue";
import type { ChatMessage, ChatResponse } from "../api/types";
import { useChat } from "./useChat";

const settings = ref({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });

const fakeResponse: ChatResponse = {
  answer: "这是回答",
  sources: [
    {
      title: "资料A",
      source_path: "a.md",
      snippet: "片段",
      evidence_ids: ["资料 1"],
      images: [],
      score: 0.9,
    },
  ],
};

function fakeSessions(initialMessages: ChatMessage[] = []) {
  const messages = ref<ChatMessage[]>(initialMessages);
  const activeId = ref("session-1");
  return {
    activeId,
    activeMessages: messages,
    clearActiveSession: () => {
      messages.value.splice(0);
    },
    touchActive: () => {
      /* no-op */
    },
  };
}

beforeEach(() => {
  settings.value = { apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" };
});

describe("useChat", () => {
  it("提问后写入用户消息和助手消息", async () => {
    const client = { chat: () => Promise.resolve(fakeResponse) };
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("如何创建采集工程？");

    expect(sessions.activeMessages.value.length).toBe(2);
    expect(sessions.activeMessages.value[0].role).toBe("user");
    expect(sessions.activeMessages.value[0].content).toBe("如何创建采集工程？");
    expect(sessions.activeMessages.value[1].role).toBe("assistant");
    expect(sessions.activeMessages.value[1].content).toBe("这是回答");
    expect(chat.selectedSource.value?.title).toBe("资料A");
    expect(chat.isAsking.value).toBe(false);
  });

  it("失败时设置错误信息且不写入助手消息", async () => {
    const client = { chat: () => Promise.reject(new Error("后端不可用")) };
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("问题");

    expect(chat.errorMessage.value).toBe("后端不可用");
    expect(sessions.activeMessages.value.length).toBe(1);
    expect(chat.isAsking.value).toBe(false);
  });

  it("重试最后一次问题", async () => {
    const client = { chat: () => Promise.resolve(fakeResponse) };
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("问题");
    await chat.retryLastQuestion();

    expect(sessions.activeMessages.value.filter((m) => m.role === "user").length).toBe(2);
  });

  it("清空当前会话", async () => {
    const client = { chat: () => Promise.resolve(fakeResponse) };
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("问题");
    chat.clearChat();

    expect(sessions.activeMessages.value.length).toBe(0);
  });

  it("空问题不发送请求", async () => {
    const client = { chat: vi.fn(() => Promise.resolve(fakeResponse)) };
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("   ");

    expect(client.chat).not.toHaveBeenCalled();
  });

  it("在途回答写入提问时的会话，即使期间切换了会话", async () => {
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, { chat: () => Promise.resolve(fakeResponse) });

    // 提问后、回答返回前切换到新会话。
    const askPromise = chat.askQuestion("问题A");
    sessions.activeId.value = "session-2";
    sessions.activeMessages.value = [];
    await askPromise;

    // 回答落在原会话，新会话保持为空。
    expect(sessions.activeMessages.value.length).toBe(0);
  });
});
