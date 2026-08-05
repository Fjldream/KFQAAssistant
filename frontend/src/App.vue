<template>
  <AppShell
    :evidence-open="activeView === 'chat' && evidenceOpen"
    :active-view="activeView"
    @view-change="handleViewChange"
  >
    <template #sidebar>
      <SidebarPanel
        :health-label="healthLabel"
        :health-state="healthState"
        :index-label="indexLabel"
        :index-state="indexState"
        :documents="indexStatus.indexStatus.value?.documents ?? 0"
        :chunks="indexStatus.indexStatus.value?.chunks ?? 0"
        :last-built-at="indexStatus.indexStatus.value?.last_built_at ?? null"
        :common-questions="commonQuestions"
        :recent-questions="history.recentQuestions.value"
        :sessions="sessions.sessions.value"
        :active-session-id="sessions.activeId.value"
        @ask="handleAsk"
        @open-settings="settingsOpen = true"
        @clear-history="history.clearQuestions"
        @remove-recent-question="history.removeQuestion"
        @new-session="sessions.createNewSession"
        @switch-session="sessions.switchSession"
        @delete-session="sessions.deleteSession"
      />
    </template>

    <ChatWorkspace
      v-if="activeView === 'chat'"
      :messages="chat.messages.value"
      :is-asking="chat.isAsking.value"
      :error-message="chat.errorMessage.value || indexStatus.errorMessage.value"
      :common-questions="commonQuestions"
      @ask="handleAsk"
      @clear="chat.clearChat"
      @retry="chat.retryLastQuestion"
      @select-source="handleSelectSource"
    />
    <EvaluationCenter v-else :client="evaluationClient" />

    <template #evidence>
      <EvidencePanel
        v-if="activeView === 'chat' && evidenceOpen"
        :sources="currentSources"
        :selected-source="chat.selectedSource.value"
        @open-material="openMaterial"
        @collapse="evidenceOpen = false"
      />
    </template>
  </AppShell>

  <SettingsDialog
    :open="settingsOpen"
    :api-base-url="settings.settings.value.apiBaseUrl"
    :api-key="settings.settings.value.apiKey"
    :theme-preference="theme.preference.value"
    @close="settingsOpen = false"
    @save="handleSaveSettings"
    @reset="settings.resetSettings"
    @theme-change="theme.setPreference"
  />

  <MaterialReader
    :source="materialSource"
    :api-base-url="settings.settings.value.apiBaseUrl"
    @close="materialSource = null"
    @preview-image="previewImage = $event"
  />

  <ImagePreview :image="previewImage" @close="previewImage = null" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { ApiSettings, SourceSnippet } from "./api/types";
import AppShell from "./components/AppShell.vue";
import ChatWorkspace from "./components/ChatWorkspace.vue";
import EvidencePanel from "./components/EvidencePanel.vue";
import ImagePreview from "./components/ImagePreview.vue";
import MaterialReader from "./components/MaterialReader.vue";
import SettingsDialog from "./components/SettingsDialog.vue";
import SidebarPanel from "./components/SidebarPanel.vue";
import { useChat } from "./composables/useChat";
import { useIndexStatus } from "./composables/useIndexStatus";
import { useLocalHistory } from "./composables/useLocalHistory";
import { useSessions } from "./composables/useSessions";
import { useSettings } from "./composables/useSettings";
import { useTheme } from "./composables/useTheme";
import { createEvaluationApiClient } from "./features/evaluation/api";
import EvaluationCenter from "./features/evaluation/EvaluationCenter.vue";

const commonQuestions = [
  "如何创建采集工程？",
  "客户端支持哪些系统？",
  "页面编辑器主要包括哪些区域？",
  "如何查看运维中心日志？",
];

const settings = useSettings();
const theme = useTheme();
const sessions = useSessions();
const history = useLocalHistory();
const chat = useChat(settings.settings, sessions);
const indexStatus = useIndexStatus(settings.settings);
const settingsOpen = ref(false);
const previewImage = ref<string | null>(null);
const materialSource = ref<SourceSnippet | null>(null);
const activeView = ref<"chat" | "evaluation">("chat");
// 资料中心默认收起：回答后点击消息里的资料 chip 才会滑出。
const evidenceOpen = ref(false);

const evaluationClient = computed(() => createEvaluationApiClient(settings.settings.value));

const healthLabel = computed(() => {
  if (indexStatus.isLoading.value) {
    return "正在检查";
  }
  return indexStatus.health.value?.status === "ok" ? "助手在线" : "后端未连接";
});

const healthState = computed<"ok" | "error" | "loading">(() => {
  if (indexStatus.isLoading.value) {
    return "loading";
  }
  return indexStatus.health.value?.status === "ok" ? "ok" : "error";
});

const indexLabel = computed(() => {
  const status = indexStatus.indexStatus.value?.status;
  if (status === "ready") {
    return "索引正常";
  }
  if (status === "stale" || status === "rebuild_required") {
    return "需要重建索引";
  }
  if (status === "empty") {
    return "索引为空";
  }
  return "等待状态";
});

const indexState = computed<"ok" | "warn" | "error" | "loading">(() => {
  const status = indexStatus.indexStatus.value?.status;
  if (status === "ready") {
    return "ok";
  }
  if (status === "stale" || status === "rebuild_required" || status === "empty") {
    return "warn";
  }
  if (status === "error") {
    return "error";
  }
  return "loading";
});

// 取最后一条助手消息的来源，作为右侧证据面板的展示内容。
const currentSources = computed<SourceSnippet[]>(() => {
  const assistantMessages = chat.messages.value.filter((message) => message.role === "assistant");
  return assistantMessages.at(-1)?.sources ?? [];
});

// 发送问题并在成功获得回答后记录到最近问题。
async function handleAsk(question: string): Promise<void> {
  const beforeCount = chat.messages.value.length;
  await chat.askQuestion(question);
  const hasNewAssistantAnswer = chat.messages.value.slice(beforeCount).some((message) => message.role === "assistant");
  if (hasNewAssistantAnswer) {
    history.addQuestion(question);
  }
}

// 保存设置后刷新后端状态，并关闭设置弹窗。
function handleSaveSettings(nextSettings: ApiSettings): void {
  settings.updateSettings(nextSettings);
  settingsOpen.value = false;
  void indexStatus.refresh();
}

// 选中证据来源：同时展开右侧资料中心并高亮该来源。
function handleSelectSource(source: SourceSnippet | null): void {
  chat.selectSource(source);
  if (source) {
    evidenceOpen.value = true;
  }
}

// 切换主工作区视图；进入评测中心时收起资料中心，避免占用报告空间。
function handleViewChange(view: "chat" | "evaluation"): void {
  activeView.value = view;
  if (view === "evaluation") {
    evidenceOpen.value = false;
  }
}

// 打开资料阅读器，并同步当前选中的资料片段。
function openMaterial(source: SourceSnippet): void {
  chat.selectSource(source);
  materialSource.value = source;
}

onMounted(() => {
  void indexStatus.refresh();
});
</script>
