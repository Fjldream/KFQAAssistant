import { beforeEach, describe, expect, it } from "vitest";
import { nextTick } from "vue";
import { useSessions } from "./useSessions";

beforeEach(() => {
  window.localStorage.clear();
});

describe("useSessions", () => {
  it("默认创建一个新会话", () => {
    const sessions = useSessions();
    expect(sessions.sessions.value.length).toBe(1);
    expect(sessions.activeSession.value?.title).toBe("新会话");
  });

  it("新建会话并切换到新会话", () => {
    const sessions = useSessions();
    sessions.createNewSession();
    expect(sessions.sessions.value.length).toBe(2);
    expect(sessions.activeId.value).toBe(sessions.sessions.value[0].id);
  });

  it("切换会话后消息数组跟随目标会话", () => {
    const sessions = useSessions();
    sessions.activeMessages.value.push({
      id: "1",
      role: "user",
      content: "问题A",
      sources: [],
      createdAt: new Date().toISOString(),
    });
    sessions.createNewSession();
    expect(sessions.activeMessages.value.length).toBe(0);
    sessions.switchSession(sessions.sessions.value[1].id);
    expect(sessions.activeMessages.value.length).toBe(1);
    expect(sessions.activeMessages.value[0].content).toBe("问题A");
  });

  it("删除会话后自动切换到剩余会话", () => {
    const sessions = useSessions();
    const firstId = sessions.sessions.value[0].id;
    sessions.createNewSession();
    const secondId = sessions.sessions.value[0].id;
    sessions.deleteSession(firstId);
    expect(sessions.sessions.value.length).toBe(1);
    expect(sessions.activeId.value).toBe(secondId);
  });

  it("删除最后一个会话后自动重建空会话", () => {
    const sessions = useSessions();
    const onlyId = sessions.sessions.value[0].id;
    sessions.deleteSession(onlyId);
    expect(sessions.sessions.value.length).toBe(1);
    expect(sessions.activeSession.value?.messages.length).toBe(0);
  });

  it("第一条用户消息自动生成会话标题", () => {
    const sessions = useSessions();
    sessions.activeMessages.value.push({
      id: "1",
      role: "user",
      content: "如何创建采集工程？",
      sources: [],
      createdAt: new Date().toISOString(),
    });
    sessions.touchActive();
    expect(sessions.activeSession.value?.title).toBe("如何创建采集工程？");
  });

  it("清空当前会话消息", () => {
    const sessions = useSessions();
    sessions.activeMessages.value.push({
      id: "1",
      role: "user",
      content: "问题",
      sources: [],
      createdAt: new Date().toISOString(),
    });
    sessions.clearActiveSession();
    expect(sessions.activeMessages.value.length).toBe(0);
  });

  it("新会话默认摘要为空并可更新", () => {
    const sessions = useSessions();

    expect(sessions.activeConversationSummary.value).toBe("");
    sessions.updateActiveConversationSummary("用户正在了解采集工程。");

    expect(sessions.activeSession.value?.conversationSummary).toBe("用户正在了解采集工程。");
  });

  it("清空当前会话时同时清空摘要", () => {
    const sessions = useSessions();
    sessions.updateActiveConversationSummary("旧摘要");

    sessions.clearActiveSession();

    expect(sessions.activeConversationSummary.value).toBe("");
  });

  it("旧会话没有摘要字段时回退为空字符串", () => {
    window.localStorage.setItem(
      "kingiask-deep.sessions",
      JSON.stringify([{ id: "old", title: "旧会话", createdAt: "now", updatedAt: "now", messages: [] }]),
    );

    const sessions = useSessions();

    expect(sessions.activeConversationSummary.value).toBe("");
  });

  it("消息变化后持久化到 localStorage", async () => {
    const sessions = useSessions();
    sessions.activeMessages.value.push({
      id: "1",
      role: "user",
      content: "问题",
      sources: [],
      createdAt: new Date().toISOString(),
    });
    sessions.touchActive();
    await nextTick();
    const raw = window.localStorage.getItem("kingiask-deep.sessions");
    expect(raw).not.toBeNull();
    expect(JSON.parse(raw as string)[0].messages.length).toBe(1);
  });
});
