import { computed, ref, type Ref } from "vue";
import { createApiClient, type StreamCallbacks } from "../api/client";
import type {
  ApiSettings,
  ChatHistoryMessage,
  ChatRequest,
  ChatResponse,
  ChatMessage,
  SourceSnippet,
} from "../api/types";
import { createId, type SessionsHandle } from "./useSessions";

export interface ChatClient {
  /** 非流式问答（保留给不支持流式的场景或兼容测试）。 */
  chat?: (request: ChatRequest) => Promise<ChatResponse>;
  /** 流式问答：逐段回调回答内容，最后回传来源与多轮摘要。 */
  chatStream: (request: ChatRequest, callbacks: StreamCallbacks) => Promise<void>;
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

// 将当前会话消息裁剪为最近 4 轮，发送给后端做追问理解。
function buildRecentMessages(messages: ChatMessage[]): ChatHistoryMessage[] {
  return messages.slice(-8).map((message) => ({ role: message.role, content: message.content }));
}

// 统计本次提问前当前会话已有几轮用户提问，用于后端控制摘要更新频率。
function countConversationTurns(messages: ChatMessage[]): number {
  return messages.filter((message) => message.role === "user").length;
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
    const requestHistory = buildRecentMessages(target);
    const requestSummary = sessions.activeConversationSummary.value;
    const requestTurnCount = countConversationTurns(target);

    target.push({
      id: createId(),
      role: "user",
      content: normalized,
      sources: [],
      createdAt: new Date().toISOString(),
    });

    // 占位助手消息：流式期间逐步填充内容，UI 据此显示打字光标。
    const assistantMessage: ChatMessage = {
      id: createId(),
      role: "assistant",
      content: "",
      sources: [],
      createdAt: new Date().toISOString(),
      streaming: true,
    };
    target.push(assistantMessage);

    try {
      await resolveClient(settings, injectedClient).chatStream(
        {
          question: normalized,
          conversation_summary: requestSummary,
          conversation_turn_count: requestTurnCount,
          recent_messages: requestHistory,
        },
        {
          onChunk: (chunk) => {
            const index = target.findIndex((message) => message.id === assistantMessage.id);
            if (index === -1) {
              return;
            }
            target[index] = { ...target[index], content: target[index].content + chunk };
          },
          onSources: (sources) => {
            const index = target.findIndex((message) => message.id === assistantMessage.id);
            if (index === -1) {
              return;
            }
            target[index] = { ...target[index], sources };
          },
          onDone: (nextSummary) => {
            const index = target.findIndex((message) => message.id === assistantMessage.id);
            if (index === -1) {
              return;
            }
            target[index] = { ...target[index], streaming: false };
            // 只有仍在原会话时才更新摘要，避免干扰其他会话。
            if (sessions.activeId.value === sessionId) {
              sessions.updateActiveConversationSummary(nextSummary || requestSummary);
            }
          },
        },
      );
      // 只有仍在原会话时才更新选中来源与会话排序，避免干扰其他会话。
      if (sessions.activeId.value === sessionId) {
        const finalMessage = target.find((message) => message.id === assistantMessage.id);
        selectedSource.value = finalMessage?.sources[0] ?? null;
        sessions.touchActive();
      }
    } catch (error) {
      errorMessage.value = toErrorMessage(error);
      // 失败时移除半成品的占位消息，只保留用户提问。
      const index = target.findIndex((message) => message.id === assistantMessage.id);
      if (index !== -1) {
        target.splice(index, 1);
      }
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
