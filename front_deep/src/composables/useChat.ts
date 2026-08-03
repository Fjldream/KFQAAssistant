import { computed, ref, type Ref } from "vue";
import { createApiClient } from "../api/client";
import type { ApiSettings, ChatRequest, ChatResponse, ChatMessage, SourceSnippet } from "../api/types";
import { createId, type SessionsHandle } from "./useSessions";

export interface ChatClient {
  chat: (request: ChatRequest) => Promise<ChatResponse>;
}

// 将未知错误转换成可显示给用户的短错误文案。
function toErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}

// 根据设置创建默认聊天客户端，测试时可以注入假客户端。
function resolveClient(settings: Ref<ApiSettings>, injectedClient?: ChatClient): ChatClient {
  return injectedClient ?? createApiClient(settings.value);
}

// 管理 KingIAsk 问答：消息写入当前会话、加载状态、错误状态和选中的证据来源。
export function useChat(
  settings: Ref<ApiSettings>,
  sessions: SessionsHandle,
  injectedClient?: ChatClient,
): {
  messages: Ref<ChatMessage[]>;
  selectedSource: Ref<SourceSnippet | null>;
  isAsking: Ref<boolean>;
  errorMessage: Ref<string | null>;
  askQuestion: (question: string) => Promise<void>;
  retryLastQuestion: () => Promise<void>;
  clearChat: () => void;
  selectSource: (source: SourceSnippet | null) => void;
} {
  const selectedSource = ref<SourceSnippet | null>(null);
  const isAsking = ref(false);
  const errorMessage = ref<string | null>(null);
  const lastQuestion = ref<string>("");

  // 会话切换时清空与旧会话绑定的选中来源。
  const messages = computed(() => sessions.activeMessages.value);

  function selectSource(source: SourceSnippet | null): void {
    selectedSource.value = source;
  }

  async function askQuestion(question: string): Promise<void> {
    const normalized = question.trim();
    if (!normalized || isAsking.value) {
      return;
    }

    lastQuestion.value = normalized;
    errorMessage.value = null;
    isAsking.value = true;

    // 捕获提问时的会话：在途请求返回时用户可能已切换/新建会话，
    // 回答必须写入提问时的会话数组，而不是当前的活跃会话。
    const sessionId = sessions.activeId.value;
    const target = sessions.activeMessages.value;

    target.push({
      id: createId(),
      role: "user",
      content: normalized,
      sources: [],
      createdAt: new Date().toISOString(),
    });

    try {
      const response = await resolveClient(settings, injectedClient).chat({ question: normalized });
      target.push({
        id: createId(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        createdAt: new Date().toISOString(),
      });
      // 只有仍在原会话时才更新选中来源与会话排序，避免干扰其他会话。
      if (sessions.activeId.value === sessionId) {
        selectedSource.value = response.sources[0] ?? null;
        sessions.touchActive();
      }
    } catch (error) {
      errorMessage.value = toErrorMessage(error);
      if (sessions.activeId.value === sessionId) {
        sessions.touchActive();
      }
    } finally {
      isAsking.value = false;
    }
  }

  async function retryLastQuestion(): Promise<void> {
    if (!lastQuestion.value) {
      return;
    }
    await askQuestion(lastQuestion.value);
  }

  function clearChat(): void {
    sessions.clearActiveSession();
    selectedSource.value = null;
    errorMessage.value = null;
    lastQuestion.value = "";
  }

  return {
    messages,
    selectedSource,
    isAsking,
    errorMessage,
    askQuestion,
    retryLastQuestion,
    clearChat,
    selectSource,
  };
}
