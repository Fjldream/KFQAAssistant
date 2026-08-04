import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import type { ChatRequest, ChatMessage, ChatResponse } from "../api/types";
import { useChat } from "./useChat";
import type { StreamCallbacks } from "../api/client";

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
  conversation_summary: "用户正在了解采集工程。",
  standalone_question: "如何创建采集工程？",
};

function fakeSessions(initialMessages: ChatMessage[] = []) {
  const messages = ref<ChatMessage[]>(initialMessages);
  const activeId = ref("session-1");
  const activeConversationSummary = ref("");
  return {
    activeId,
    activeMessages: messages,
    activeConversationSummary,
    updateActiveConversationSummary: (summary: string) => {
      activeConversationSummary.value = summary;
    },
    clearActiveSession: () => {
      messages.value.splice(0);
      activeConversationSummary.value = "";
    },
    touchActive: () => {
      /* no-op */
    },
  };
}

// 构造流式假客户端：逐段回调 chunk，再回传 sources 与摘要。
function fakeStreamClient(response: ChatResponse = fakeResponse) {
  return {
    chat: vi.fn(),
    chatStream: vi.fn((_request: ChatRequest, callbacks: StreamCallbacks) => {
      callbacks.onChunk(response.answer);
      callbacks.onSources(response.sources);
      callbacks.onDone(response.conversation_summary ?? "", response.standalone_question ?? "");
      return Promise.resolve();
    }),
  };
}

beforeEach(() => {
  settings.value = { apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" };
});

describe("useChat", () => {
  it("提问后写入用户消息并流式填充助手消息", async () => {
    const client = fakeStreamClient();
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("如何创建采集工程？");

    expect(sessions.activeMessages.value.length).toBe(2);
    expect(sessions.activeMessages.value[0].role).toBe("user");
    expect(sessions.activeMessages.value[0].content).toBe("如何创建采集工程？");
    const assistant = sessions.activeMessages.value[1];
    expect(assistant.role).toBe("assistant");
    expect(assistant.content).toBe("这是回答");
    expect(assistant.streaming).toBe(false);
    expect(assistant.sources[0].title).toBe("资料A");
    expect(chat.selectedSource.value?.title).toBe("资料A");
    expect(chat.isAsking.value).toBe(false);
  });

  it("chunk 分多次到达时内容逐步累积", async () => {
    const client = {
      chat: vi.fn(),
      chatStream: vi.fn((_request: ChatRequest, callbacks: StreamCallbacks) => {
        callbacks.onChunk("点击");
        callbacks.onChunk("新建工程。");
        callbacks.onSources([]);
        callbacks.onDone("", "");
        return Promise.resolve();
      }),
    };
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("问题");

    expect(sessions.activeMessages.value[1].content).toBe("点击新建工程。");
  });

  it("失败时移除半成品占位消息并设置错误信息", async () => {
    const client = {
      chat: vi.fn(),
      chatStream: vi.fn(() => Promise.reject(new Error("后端不可用"))),
    };
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("问题");

    expect(chat.errorMessage.value).toBe("后端不可用");
    // 用户消息保留，半成品助手消息被移除。
    expect(sessions.activeMessages.value.length).toBe(1);
    expect(sessions.activeMessages.value[0].role).toBe("user");
    expect(chat.isAsking.value).toBe(false);
  });

  it("重试最后一次问题", async () => {
    const client = fakeStreamClient();
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("问题");
    await chat.retryLastQuestion();

    expect(sessions.activeMessages.value.filter((m) => m.role === "user").length).toBe(2);
  });

  it("清空当前会话", async () => {
    const client = fakeStreamClient();
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("问题");
    chat.clearChat();

    expect(sessions.activeMessages.value.length).toBe(0);
  });

  it("提问时发送摘要和最近消息，并保存返回的新摘要", async () => {
    const existingMessages: ChatMessage[] = [
      { id: "1", role: "user", content: "如何创建采集工程？", sources: [], createdAt: "1" },
      { id: "2", role: "assistant", content: "点击新建工程。", sources: [], createdAt: "2" },
    ];
    const sessions = fakeSessions(existingMessages);
    sessions.activeConversationSummary.value = "用户正在了解采集工程创建流程。";
    const client = fakeStreamClient();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("那怎么运行？");

    expect(client.chatStream).toHaveBeenCalledWith(
      {
        question: "那怎么运行？",
        conversation_summary: "用户正在了解采集工程创建流程。",
        conversation_turn_count: 1,
        recent_messages: [
          { role: "user", content: "如何创建采集工程？" },
          { role: "assistant", content: "点击新建工程。" },
        ],
      },
      expect.any(Object),
    );
    expect(sessions.activeConversationSummary.value).toBe("用户正在了解采集工程。");
  });

  it("空问题不发送请求", async () => {
    const client = fakeStreamClient();
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, client);

    await chat.askQuestion("   ");

    expect(client.chatStream).not.toHaveBeenCalled();
  });

  it("在途回答写入提问时的会话，即使期间切换了会话", async () => {
    const sessions = fakeSessions();
    const chat = useChat(settings, sessions, fakeStreamClient());

    // 提问后、回答返回前切换到新会话。
    const askPromise = chat.askQuestion("问题A");
    sessions.activeId.value = "session-2";
    sessions.activeMessages.value = [];
    await askPromise;

    // 回答落在原会话，新会话保持为空。
    expect(sessions.activeMessages.value.length).toBe(0);
  });
});
