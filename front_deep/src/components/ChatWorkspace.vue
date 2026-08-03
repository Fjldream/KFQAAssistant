<template>
  <section class="ka-chat">
    <header class="ka-chat__head">
      <div>
        <h1>KingIAsk 产品知识助手</h1>
        <p>基于 KF 产品手册回答操作、配置和排障问题</p>
      </div>
      <button class="ka-button ka-button--ghost" type="button" @click="emit('clear')">
        <Trash2 :size="15" aria-hidden="true" />
        清空会话
      </button>
    </header>

    <div class="ka-messages" ref="messageListEl" aria-live="polite">
      <div v-if="messages.length === 0" class="ka-welcome">
        <div class="ka-welcome__mark" aria-hidden="true">K</div>
        <h2>询问 KF 产品手册中的操作问题</h2>
        <p class="ka-welcome__desc">
          回答会显示在这里，右侧同步展示来源片段、相似度和相关图片，帮助您核对答案依据。
        </p>
        <div class="ka-welcome__starters">
          <button
            v-for="question in commonQuestions"
            :key="question"
            class="ka-starter"
            type="button"
            data-testid="welcome-starter"
            @click="emit('ask', question)"
          >
            <span>{{ question }}</span>
            <ArrowUpRight :size="16" class="ka-starter__arrow" aria-hidden="true" />
          </button>
        </div>
      </div>

      <template v-else>
        <article
          v-for="message in messages"
          :key="message.id"
          class="ka-msg"
          :class="`ka-msg--${message.role}`"
        >
          <div v-if="message.role === 'assistant'" class="ka-msg__avatar" aria-hidden="true">
            <Sparkles :size="15" />
          </div>

          <div class="ka-msg__body">
            <div class="ka-msg__meta">
              {{ message.role === "user" ? "你" : "KingIAsk" }}
              <span>·</span>
              <span>{{ formatTime(message.createdAt) }}</span>
            </div>

            <div
              v-if="message.role === 'assistant'"
              class="ka-msg__bubble"
              v-html="renderMarkdown(message.content)"
            ></div>
            <div v-else class="ka-msg__bubble">{{ message.content }}</div>

            <div v-if="message.role === 'assistant'" class="ka-msg__actions">
              <button class="ka-msg__action" type="button" @click="copyAnswer(message.content)">
                <Copy :size="14" aria-hidden="true" />
                复制
              </button>
              <button
                v-for="source in message.sources"
                :key="source.source_path"
                class="ka-source-chip"
                type="button"
                @click="emit('selectSource', source)"
              >
                {{ source.evidence_ids[0] || "资料" }} · {{ source.title }}
              </button>
            </div>
          </div>
        </article>

        <article v-if="isAsking" class="ka-msg ka-msg--assistant" aria-label="KingIAsk 正在思考">
          <div class="ka-msg__avatar" aria-hidden="true">
            <Sparkles :size="15" />
          </div>
          <div class="ka-msg__body">
            <div class="ka-msg__meta">KingIAsk</div>
            <div class="ka-msg__bubble">
              <div class="ka-thinking">
                <span class="ka-thinking__orbits" aria-hidden="true">
                  <span class="ka-thinking__dot"></span>
                  <span class="ka-thinking__dot"></span>
                  <span class="ka-thinking__dot"></span>
                </span>
                <div class="ka-thinking__text">
                  <strong>正在检索手册</strong>
                  <span>整理依据并组织回答</span>
                </div>
              </div>
            </div>
          </div>
        </article>
      </template>
    </div>

    <p v-if="errorMessage" class="ka-error" role="alert">
      <AlertCircle :size="15" aria-hidden="true" />
      <span>{{ errorMessage }}</span>
    </p>

    <form class="ka-composer" @submit.prevent="submitQuestion">
      <textarea
        v-model="draft"
        rows="1"
        ref="textareaEl"
        placeholder="输入 KF 产品使用问题，Enter 发送"
        :disabled="isAsking"
        aria-label="向 KingIAsk 提问"
        @keydown.enter="handleEnter"
        @input="autoGrow"
      ></textarea>
      <div class="ka-composer__bar">
        <span class="ka-composer__hint">Enter 发送 · Shift + Enter 换行</span>
        <div class="ka-composer__actions">
          <button class="ka-button ka-button--ghost" type="button" :disabled="isAsking" @click="emit('retry')">
            <RefreshCcw :size="14" aria-hidden="true" />
            重试
          </button>
          <button class="ka-button ka-button--primary" type="submit" :disabled="isAsking || !draft.trim()">
            <span v-if="isAsking" class="ka-spin">
              <LoaderCircle :size="15" aria-hidden="true" />
            </span>
            <Send v-else :size="15" aria-hidden="true" />
            {{ isAsking ? "思考中" : "提问" }}
          </button>
        </div>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";
import {
  AlertCircle,
  ArrowUpRight,
  Copy,
  LoaderCircle,
  RefreshCcw,
  Send,
  Sparkles,
  Trash2,
} from "lucide-vue-next";
import { nextTick, ref, watch } from "vue";
import type { ChatMessage, SourceSnippet } from "../api/types";

const props = defineProps<{
  messages: ChatMessage[];
  isAsking: boolean;
  errorMessage: string | null;
  commonQuestions: string[];
}>();

const emit = defineEmits<{
  ask: [question: string];
  clear: [];
  retry: [];
  selectSource: [source: SourceSnippet];
}>();

const draft = ref("");
const textareaEl = ref<HTMLTextAreaElement | null>(null);
const messageListEl = ref<HTMLElement | null>(null);

// 安全渲染 Markdown：禁止原始 HTML，白名单链接协议，再经 DOMPurify 消毒。
// 回答内容来自后端检索结果并持久化在 localStorage，必须做双重防御。
const markdown = new MarkdownIt({
  breaks: true,
  linkify: true,
  html: false,
});
// 只允许 http/https/mailto/锚点/相对链接，阻止 javascript: 等危险协议。
markdown.validateLink = (url: string) => /^(https?:|mailto:|#|\/)/i.test(url);

// 新消息出现时自动滚动到底部，保持最新内容可见。
watch(
  () => props.messages.length,
  async () => {
    await nextTick();
    const el = messageListEl.value;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  },
);

// 将 Markdown 回答转换为安全 HTML，用于展示模型返回的步骤和列表。
function renderMarkdown(content: string): string {
  return DOMPurify.sanitize(markdown.render(content));
}

// 提交当前输入的问题，并清空输入框、重置高度。
function submitQuestion(): void {
  const question = draft.value.trim();
  if (!question) {
    return;
  }
  emit("ask", question);
  draft.value = "";
  requestAnimationFrame(autoGrow);
}

// 处理输入框回车：Enter 发送，Shift+Enter 保留换行。
function handleEnter(event: KeyboardEvent): void {
  if (event.shiftKey || event.isComposing || event.keyCode === 229) {
    return;
  }
  event.preventDefault();
  submitQuestion();
}

// 输入框随内容自动增高，最多 180px（CSS max-height 约束）。
function autoGrow(): void {
  const el = textareaEl.value;
  if (!el) {
    return;
  }
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
}

// 复制回答文本，浏览器不支持剪贴板时静默跳过。
function copyAnswer(content: string): void {
  void navigator.clipboard?.writeText(content);
}

// 将 ISO 时间格式化为本地 HH:mm 短时间。
function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}
</script>
