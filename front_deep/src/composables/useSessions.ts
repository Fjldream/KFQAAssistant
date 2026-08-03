import { computed, ref, watch, type Ref } from "vue";
import type { ChatMessage, ChatSession } from "../api/types";

const SESSIONS_KEY = "kingiask-deep.sessions";
const MAX_SESSIONS = 30;
const DEFAULT_TITLE = "新会话";

// useChat 等调用方依赖的会话句柄子集。
export interface SessionsHandle {
  activeId: Ref<string>;
  activeMessages: Ref<ChatMessage[]>;
  clearActiveSession: () => void;
  touchActive: () => void;
}

// 生成会话 / 消息 ID，用时间和随机数降低同一毫秒重复概率。
export function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function createSession(title = DEFAULT_TITLE): ChatSession {
  const now = new Date().toISOString();
  return {
    id: createId(),
    title,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

// 从 localStorage 读取会话列表；没有或解析失败时创建一个空会话。
function loadSessions(): ChatSession[] {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(SESSIONS_KEY);
  } catch {
    // 存储被禁用（隐私模式/权限）时直接回退到空会话，避免白屏。
    return [createSession()];
  }
  if (!raw) {
    return [createSession()];
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [createSession()];
    }
    // 只保留结构完整的会话：必须带 id 且 messages 为数组。
    const valid = parsed.filter(
      (item): item is ChatSession =>
        Boolean(item && typeof item === "object" && "id" in item && Array.isArray((item as ChatSession).messages)),
    );
    return valid.length > 0 ? valid.slice(0, MAX_SESSIONS) : [createSession()];
  } catch {
    return [createSession()];
  }
}

function saveSessions(sessions: ChatSession[]): void {
  try {
    window.localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)));
  } catch {
    // 存储不可用时静默失败，不影响当前会话使用。
  }
}

// 管理多会话的创建、切换、删除和消息读写，全部持久化到 localStorage。
// 会话列表展示的是完整对话历史，比单条问题记录更适合企业级使用。
export function useSessions() {
  const sessions = ref<ChatSession[]>(loadSessions());
  const activeId = ref<string>(sessions.value[0]?.id ?? "");

  // 当前会话的消息数组：直接引用 session.messages，push 即可同时更新会话与 UI。
  const activeMessages = ref<ChatMessage[]>(sessions.value.find((s) => s.id === activeId.value)?.messages ?? []);

  const activeSession = computed<ChatSession | null>(
    () => sessions.value.find((s) => s.id === activeId.value) ?? null,
  );

  // 深层监听会话变化并持久化，切换会话后由 UI 主动调用 touch 更新排序。
  watch(sessions, (next) => saveSessions(next), { deep: true });

  function switchSession(id: string): void {
    const target = sessions.value.find((s) => s.id === id);
    if (!target) {
      return;
    }
    activeId.value = id;
    activeMessages.value = target.messages;
  }

  function createNewSession(): void {
    const session = createSession();
    sessions.value.unshift(session);
    activeId.value = session.id;
    activeMessages.value = session.messages;
  }

  function deleteSession(id: string): void {
    const index = sessions.value.findIndex((s) => s.id === id);
    if (index === -1) {
      return;
    }
    sessions.value.splice(index, 1);
    if (sessions.value.length === 0) {
      sessions.value.push(createSession());
    }
    if (activeId.value === id) {
      const next = sessions.value[0];
      activeId.value = next.id;
      activeMessages.value = next.messages;
    }
  }

  function clearActiveSession(): void {
    activeMessages.value.splice(0, activeMessages.value.length);
    touchActive();
  }

  // 会话有内容变化时更新 updatedAt，用于列表排序（最近在最前）。
  function touchActive(): void {
    const session = activeSession.value;
    if (!session) {
      return;
    }
    session.updatedAt = new Date().toISOString();
    if (session.title === DEFAULT_TITLE && session.messages.length > 0) {
      const firstUser = session.messages.find((m) => m.role === "user");
      if (firstUser) {
        session.title = firstUser.content.length > 18 ? `${firstUser.content.slice(0, 18)}…` : firstUser.content;
      }
    }
    // 重新排序：当前会话置顶。
    sessions.value.sort((a, b) => (a.id === activeId.value ? -1 : b.id === activeId.value ? 1 : 0));
  }

  return {
    sessions,
    activeId,
    activeSession,
    activeMessages,
    switchSession,
    createNewSession,
    deleteSession,
    clearActiveSession,
    touchActive,
  };
}
