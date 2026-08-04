import { beforeEach, describe, expect, it } from "vitest";
import { useLocalHistory } from "./useLocalHistory";

beforeEach(() => {
  window.localStorage.clear();
});

describe("useLocalHistory", () => {
  it("添加问题后置顶并去重", () => {
    const history = useLocalHistory();
    history.addQuestion("问题A");
    history.addQuestion("问题B");
    history.addQuestion("问题A");
    expect(history.recentQuestions.value).toEqual(["问题A", "问题B"]);
  });

  it("清空最近问题", () => {
    const history = useLocalHistory();
    history.addQuestion("问题A");
    history.clearQuestions();
    expect(history.recentQuestions.value).toEqual([]);
  });

  it("删除单条最近问题", () => {
    const history = useLocalHistory();
    history.addQuestion("问题A");
    history.addQuestion("问题B");
    history.addQuestion("问题C");
    history.removeQuestion("问题B");
    expect(history.recentQuestions.value).toEqual(["问题C", "问题A"]);
  });

  it("空问题不记录", () => {
    const history = useLocalHistory();
    history.addQuestion("  ");
    expect(history.recentQuestions.value).toEqual([]);
  });
});
