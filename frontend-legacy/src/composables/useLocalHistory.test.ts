import { beforeEach, describe, expect, it } from "vitest";
import { useLocalHistory } from "./useLocalHistory";

describe("useLocalHistory", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("deduplicates and keeps recent questions newest first", () => {
    const history = useLocalHistory();

    history.addQuestion("如何创建采集工程？");
    history.addQuestion("客户端支持哪些系统？");
    history.addQuestion("如何创建采集工程？");

    expect(history.recentQuestions.value).toEqual(["如何创建采集工程？", "客户端支持哪些系统？"]);
  });
});
