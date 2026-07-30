<template>
  <AppShell>
    <template #sidebar>
      <LeftSidebar
        :health-label="healthLabel"
        :index-label="indexLabel"
        :documents="indexStatus.indexStatus.value?.documents ?? 0"
        :chunks="indexStatus.indexStatus.value?.chunks ?? 0"
        :last-built-at="indexStatus.indexStatus.value?.last_built_at ?? null"
        :common-questions="commonQuestions"
        :recent-questions="history.recentQuestions.value"
        @ask="handleAsk"
        @open-settings="settingsOpen = true"
        @clear-history="history.clearQuestions"
      />
    </template>

    <ChatWorkspace
      :messages="chat.messages.value"
      :is-asking="chat.isAsking.value"
      :error-message="chat.errorMessage.value || indexStatus.errorMessage.value"
      @ask="handleAsk"
      @clear="chat.clearChat"
      @retry="chat.retryLastQuestion"
      @select-source="chat.selectSource"
    />

    <template #evidence>
      <EvidencePanel
        :sources="currentSources"
        :selected-source="chat.selectedSource.value"
        @open-material="openMaterial"
      />
    </template>
  </AppShell>

  <SettingsDialog
    :open="settingsOpen"
    :api-base-url="settings.settings.value.apiBaseUrl"
    :api-key="settings.settings.value.apiKey"
    @close="settingsOpen = false"
    @save="handleSaveSettings"
    @reset="settings.resetSettings"
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
import LeftSidebar from "./components/LeftSidebar.vue";
import MaterialReader from "./components/MaterialReader.vue";
import SettingsDialog from "./components/SettingsDialog.vue";
import { useChat } from "./composables/useChat";
import { useIndexStatus } from "./composables/useIndexStatus";
import { useLocalHistory } from "./composables/useLocalHistory";
import { useSettings } from "./composables/useSettings";

const commonQuestions = [
  "如何创建采集工程？",
  "客户端支持哪些系统？",
  "页面编辑器主要包括哪些区域？",
  "如何查看运维中心日志？",
];

const settings = useSettings();
const history = useLocalHistory();
const chat = useChat(settings.settings);
const indexStatus = useIndexStatus(settings.settings);
const settingsOpen = ref(false);
const previewImage = ref<string | null>(null);
const materialSource = ref<SourceSnippet | null>(null);

const healthLabel = computed(() => {
  if (indexStatus.isLoading.value) {
    return "正在检查";
  }
  return indexStatus.health.value?.status === "ok" ? "后端在线" : "后端未连接";
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

const currentSources = computed<SourceSnippet[]>(() => {
  const assistantMessages = chat.messages.value.filter((message) => message.role === "assistant");
  return assistantMessages.at(-1)?.sources ?? [];
});

// 发送问题并在成功获得回答后记录到最近会话。
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

// 打开整页资料阅读器，并同步当前选中的资料片段。
function openMaterial(source: SourceSnippet): void {
  chat.selectSource(source);
  materialSource.value = source;
}

onMounted(() => {
  void indexStatus.refresh();
});
</script>
