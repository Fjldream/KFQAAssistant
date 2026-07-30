<template>
  <div class="ki-sidebar-panel">
    <header class="ki-sidebar-header">
      <div class="ki-brand-lockup">
        <div class="ki-brand-mark" aria-hidden="true">K</div>
        <div>
          <p class="ki-brand">KingIAsk</p>
          <p class="ki-subtitle">KF 产品知识问答助手</p>
        </div>
      </div>
      <button class="ki-icon-button" type="button" title="设置" @click="emit('openSettings')">
        <Settings :size="18" aria-hidden="true" />
      </button>
    </header>

    <section class="ki-sidebar-section" aria-label="知识库状态">
      <div class="ki-section-heading">
        <p class="ki-section-title">知识库状态</p>
        <span class="ki-status-badge">Live</span>
      </div>
      <div class="ki-status-row">
        <span class="ki-status-dot" aria-hidden="true"></span>
        <div>
          <strong>{{ healthLabel }}</strong>
          <span>{{ indexLabel }}</span>
        </div>
      </div>
      <dl class="ki-metric-list">
        <div>
          <dt>文档</dt>
          <dd>{{ documents }}</dd>
        </div>
        <div>
          <dt>Chunks</dt>
          <dd>{{ chunks }}</dd>
        </div>
      </dl>
      <p class="ki-small-text">最后构建：{{ formatLastBuiltAt(lastBuiltAt) }}</p>
    </section>

    <section class="ki-sidebar-section" aria-label="常用问题">
      <p class="ki-section-title">常用问题</p>
      <button
        v-for="question in commonQuestions"
        :key="question"
        class="ki-question-button"
        type="button"
        data-testid="common-question"
        @click="emit('ask', question)"
      >
        <span>{{ question }}</span>
        <span aria-hidden="true">↗</span>
      </button>
    </section>

    <section class="ki-sidebar-section" aria-label="最近会话">
      <div class="ki-section-heading">
        <p class="ki-section-title">最近会话</p>
        <button class="ki-text-button" type="button" @click="emit('clearHistory')">清空</button>
      </div>
      <p v-if="recentQuestions.length === 0" class="ki-empty-text">暂无最近问题</p>
      <button
        v-for="question in recentQuestions"
        v-else
        :key="question"
        class="ki-question-button"
        type="button"
        @click="emit('ask', question)"
      >
        <span>{{ question }}</span>
        <span aria-hidden="true">↗</span>
      </button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Settings } from "lucide-vue-next";

defineProps<{
  healthLabel: string;
  indexLabel: string;
  documents: number;
  chunks: number;
  lastBuiltAt: string | null;
  commonQuestions: string[];
  recentQuestions: string[];
}>();

const emit = defineEmits<{
  ask: [question: string];
  openSettings: [];
  clearHistory: [];
}>();

// 将后端 ISO 时间转换为适合侧边栏展示的短时间格式。
function formatLastBuiltAt(value: string | null): string {
  if (!value) {
    return "暂未获取";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${minute}`;
}
</script>
