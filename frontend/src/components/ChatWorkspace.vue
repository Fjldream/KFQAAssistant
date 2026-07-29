<template>
  <section class="ki-chat-workspace">
    <header class="ki-chat-header">
      <div>
        <p class="ki-section-title">问答工作区</p>
        <h1>产品使用问题</h1>
      </div>
      <button class="ki-secondary-button" type="button" @click="emit('clear')">清空会话</button>
    </header>

    <div class="ki-message-list" aria-live="polite">
      <div v-if="messages.length === 0" class="ki-welcome-state">
        <p class="ki-section-title">开始提问</p>
        <h2>询问 KF 产品手册中的操作问题</h2>
        <p>回答会显示在这里，右侧会同步展示来源片段和相关图片。</p>
      </div>

      <article
        v-for="message in messages"
        :key="message.id"
        class="ki-message"
        :class="`ki-message--${message.role}`"
      >
        <div class="ki-message-meta">{{ message.role === "user" ? "你" : "KingIAsk" }}</div>
        <div v-if="message.role === 'assistant'" class="ki-message-content" v-html="renderMarkdown(message.content)"></div>
        <p v-else class="ki-message-content">{{ message.content }}</p>

        <div v-if="message.role === 'assistant'" class="ki-message-actions">
          <button class="ki-icon-text-button" type="button" @click="copyAnswer(message.content)">
            <Copy :size="15" aria-hidden="true" />
            复制
          </button>
          <button
            v-for="source in message.sources"
            :key="source.source_path"
            class="ki-source-chip"
            type="button"
            @click="emit('selectSource', source)"
          >
            {{ source.evidence_ids[0] || "资料" }} · {{ source.title }}
          </button>
        </div>
      </article>

      <article
        v-if="isAsking"
        class="ki-message ki-message--assistant ki-thinking-message"
        aria-label="KingIAsk 正在思考"
      >
        <div class="ki-message-meta">KingIAsk</div>
        <div class="ki-thinking-content">
          <span class="ki-thinking-orbit" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </span>
          <div>
            <strong>正在检索手册</strong>
            <p>整理依据并组织回答</p>
          </div>
        </div>
      </article>
    </div>

    <p v-if="errorMessage" class="ki-error-text">{{ errorMessage }}</p>

    <form class="ki-input-bar" @submit.prevent="submitQuestion">
      <textarea
        v-model="draft"
        rows="2"
        placeholder="输入 KF 产品使用问题"
        :disabled="isAsking"
        @keydown.enter="handleEnter"
      ></textarea>
      <div class="ki-input-actions">
        <button class="ki-secondary-button" type="button" :disabled="isAsking" @click="emit('retry')">
          <RefreshCcw :size="16" aria-hidden="true" />
          重试
        </button>
        <button class="ki-primary-button" type="submit" :disabled="isAsking || !draft.trim()">
          <span v-if="isAsking" class="ki-button-spinner" aria-hidden="true"></span>
          <Send v-else :size="16" aria-hidden="true" />
          {{ isAsking ? "思考中" : "提问" }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import MarkdownIt from "markdown-it";
import { Copy, RefreshCcw, Send } from "lucide-vue-next";
import { ref } from "vue";
import type { ChatMessage, SourceSnippet } from "../api/types";

defineProps<{
  messages: ChatMessage[];
  isAsking: boolean;
  errorMessage: string | null;
}>();

const emit = defineEmits<{
  ask: [question: string];
  clear: [];
  retry: [];
  selectSource: [source: SourceSnippet];
}>();

const draft = ref("");
const markdown = new MarkdownIt({ breaks: true, linkify: true });

// 将 Markdown 回答转换为 HTML，用于展示模型返回的步骤和列表。
function renderMarkdown(content: string): string {
  return markdown.render(content);
}

// 提交当前输入的问题，并清空输入框。
function submitQuestion(): void {
  const question = draft.value.trim();
  if (!question) {
    return;
  }
  emit("ask", question);
  draft.value = "";
}

// 处理输入框回车：Enter 发送，Shift+Enter 保留换行。
function handleEnter(event: KeyboardEvent): void {
  if (event.shiftKey) {
    return;
  }
  event.preventDefault();
  submitQuestion();
}

// 复制回答文本，浏览器不支持剪贴板时静默跳过。
function copyAnswer(content: string): void {
  void navigator.clipboard?.writeText(content);
}
</script>
