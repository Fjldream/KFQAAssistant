import { ref, type Ref } from "vue";

const RECENT_QUESTIONS_KEY = "kingiask.recentQuestions";
const MAX_RECENT_QUESTIONS = 20;

// 从 localStorage 读取最近问题列表，异常时返回空列表。
function loadRecentQuestions(): string[] {
  const raw = window.localStorage.getItem(RECENT_QUESTIONS_KEY);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

// 保存最近问题列表，最多保留固定数量，避免本地存储无限增长。
function saveRecentQuestions(questions: string[]): void {
  window.localStorage.setItem(RECENT_QUESTIONS_KEY, JSON.stringify(questions.slice(0, MAX_RECENT_QUESTIONS)));
}

// 管理本地最近问题记录，按最新优先排序并自动去重。
export function useLocalHistory(): {
  recentQuestions: Ref<string[]>;
  addQuestion: (question: string) => void;
  clearQuestions: () => void;
} {
  const recentQuestions = ref<string[]>(loadRecentQuestions());

  function addQuestion(question: string): void {
    const normalized = question.trim();
    if (!normalized) {
      return;
    }
    recentQuestions.value = [
      normalized,
      ...recentQuestions.value.filter((existing) => existing !== normalized),
    ].slice(0, MAX_RECENT_QUESTIONS);
    saveRecentQuestions(recentQuestions.value);
  }

  function clearQuestions(): void {
    recentQuestions.value = [];
    saveRecentQuestions(recentQuestions.value);
  }

  return {
    recentQuestions,
    addQuestion,
    clearQuestions,
  };
}
