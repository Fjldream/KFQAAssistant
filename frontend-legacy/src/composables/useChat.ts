import { ref, type Ref } from "vue";
import { createApiClient } from "../api/client";
import type { ApiSettings, ChatMessage, ChatRequest, ChatResponse, SourceSnippet } from "../api/types";

export interface ChatClient {
  chat: (request: ChatRequest) => Promise<ChatResponse>;
}

// 生成前端消息 ID，用时间和随机数降低同一毫秒重复概率。
function createMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
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

// 管理 KingIAsk 问答消息、加载状态、错误状态和当前选中的证据来源。
export function useChat(
  settings: Ref<ApiSettings>,
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
  const messages = ref<ChatMessage[]>([]);
  const selectedSource = ref<SourceSnippet | null>(null);
  const isAsking = ref(false);
  const errorMessage = ref<string | null>(null);
  const lastQuestion = ref<string>("");

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
    messages.value.push({
      id: createMessageId(),
      role: "user",
      content: normalized,
      sources: [],
      createdAt: new Date().toISOString(),
    });

    try {
      const response = await resolveClient(settings, injectedClient).chat({ question: normalized });
      messages.value.push({
        id: createMessageId(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        createdAt: new Date().toISOString(),
      });
      selectedSource.value = response.sources[0] ?? null;
    } catch (error) {
      errorMessage.value = toErrorMessage(error);
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
    messages.value = [];
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
