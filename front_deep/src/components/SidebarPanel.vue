<template>
  <div class="ka-sidebar">
    <header class="ka-sidebar__head">
      <div class="ka-brand">
        <div class="ka-brand__mark" aria-hidden="true">K</div>
        <div>
          <p class="ka-brand__name">KingIAsk</p>
          <p class="ka-brand__sub">KF 产品知识问答助手</p>
        </div>
      </div>
      <button class="ka-icon-button" type="button" title="设置" @click="emit('openSettings')">
        <Settings :size="18" aria-hidden="true" />
      </button>
    </header>

    <div class="ka-sidebar__scroll">
      <section class="ka-section" aria-label="知识库状态">
        <div class="ka-status">
          <div class="ka-status__main">
            <span class="ka-status__dot" :data-state="healthState" aria-hidden="true"></span>
            <span class="ka-status__health">{{ healthLabel }}</span>
            <span class="ka-status__divider" aria-hidden="true">·</span>
            <span class="ka-status__index" :data-state="indexState">{{ indexLabel }}</span>
          </div>
          <div class="ka-status__metrics">
            <span class="ka-status__metric">文档 <strong>{{ documents }}</strong></span>
            <span class="ka-status__metric">Chunks <strong>{{ chunks }}</strong></span>
          </div>
          <p class="ka-status__built">向量库更新于 {{ formatLastBuiltAt(lastBuiltAt) }}</p>
        </div>
      </section>

      <section class="ka-section" aria-label="会话">
        <div class="ka-section__head">
          <p class="ka-eyebrow">会话</p>
          <button class="ka-section__action" type="button" @click="emit('newSession')">＋ 新建</button>
        </div>
        <p v-if="sessions.length === 0" class="ka-empty">暂无会话</p>
        <div v-else class="ka-list" data-testid="session-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="ka-session"
            :class="{ 'is-active': session.id === activeSessionId }"
          >
            <button
              class="ka-session__main"
              type="button"
              data-testid="session-item"
              @click="emit('switchSession', session.id)"
            >
              <MessageSquare :size="15" class="ka-list-item__icon" aria-hidden="true" />
              <span class="ka-list-item__text">{{ session.title }}</span>
            </button>
            <button
              class="ka-session__del"
              type="button"
              :aria-label="`删除会话 ${session.title}`"
              title="删除会话"
              @click="emit('deleteSession', session.id)"
            >
              <X :size="14" aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>

      <section class="ka-section" aria-label="常用问题">
        <p class="ka-eyebrow">常用问题</p>
        <div class="ka-list">
          <button
            v-for="question in commonQuestions"
            :key="question"
            class="ka-list-item"
            type="button"
            data-testid="common-question"
            @click="emit('ask', question)"
          >
            <Sparkles :size="15" class="ka-list-item__icon" aria-hidden="true" />
            <span class="ka-list-item__text">{{ question }}</span>
          </button>
        </div>
      </section>

      <section class="ka-section" aria-label="最近提问">
        <div class="ka-section__head">
          <p class="ka-eyebrow">最近提问</p>
          <button class="ka-section__action" type="button" @click="emit('clearHistory')">清空</button>
        </div>
        <p v-if="recentQuestions.length === 0" class="ka-empty">暂无最近提问</p>
        <div v-else class="ka-list" data-testid="recent-list">
          <button
            v-for="question in recentQuestions"
            :key="question"
            class="ka-list-item"
            type="button"
            @click="emit('ask', question)"
          >
            <Clock :size="15" class="ka-list-item__icon" aria-hidden="true" />
            <span class="ka-list-item__text">{{ question }}</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Clock, MessageSquare, Settings, Sparkles, X } from "lucide-vue-next";
import type { ChatSession } from "../api/types";

defineProps<{
  healthLabel: string;
  healthState: "ok" | "error" | "loading";
  indexLabel: string;
  indexState: "ok" | "warn" | "error" | "loading";
  documents: number;
  chunks: number;
  lastBuiltAt: string | null;
  commonQuestions: string[];
  recentQuestions: string[];
  sessions: ChatSession[];
  activeSessionId: string;
}>();

const emit = defineEmits<{
  ask: [question: string];
  openSettings: [];
  clearHistory: [];
  newSession: [];
  switchSession: [id: string];
  deleteSession: [id: string];
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
