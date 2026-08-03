import { nextTick, ref } from "vue";
import { describe, expect, it, vi } from "vitest";
import type { ApiSettings, ChatResponse } from "../api/types";
import { useChat } from "./useChat";

describe("useChat", () => {
  it("adds user and assistant messages after a successful answer", async () => {
    const response: ChatResponse = {
      answer: "创建采集工程需要点击新建工程。",
      sources: [
        {
          title: "工程开发-Windows",
          source_path: "html/数采管理/工程开发-Windows/index.html",
          snippet: "点击新建工程按钮。",
          evidence_ids: ["资料 1"],
          images: ["html/数采管理/工程开发-Windows/1.png"],
          score: 0.82,
        },
      ],
    };
    const ask = vi.fn().mockResolvedValue(response);
    const settings = ref<ApiSettings>({ apiBaseUrl: "http://127.0.0.1:8000", apiKey: "" });
    const chat = useChat(settings, { chat: ask });

    await chat.askQuestion("如何创建采集工程？");
    await nextTick();

    expect(ask).toHaveBeenCalledWith({ question: "如何创建采集工程？" });
    expect(chat.messages.value).toHaveLength(2);
    expect(chat.messages.value[0].role).toBe("user");
    expect(chat.messages.value[1].role).toBe("assistant");
    expect(chat.messages.value[1].sources[0].images).toEqual(["html/数采管理/工程开发-Windows/1.png"]);
    expect(chat.selectedSource.value?.title).toBe("工程开发-Windows");
  });
});
