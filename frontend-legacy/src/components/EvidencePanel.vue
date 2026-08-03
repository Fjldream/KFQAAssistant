<template>
  <section class="ki-evidence-panel ki-evidence-inspector">
    <header class="ki-evidence-header">
      <p class="ki-section-title">资料与图片</p>
      <h2>资料中心</h2>
      <span>{{ sources.length }} 个资料片段</span>
    </header>

    <div v-if="sources.length === 0" class="ki-empty-block ki-evidence-empty">
      <p>暂无资料</p>
      <span>提问后会显示手册段落、路径和相关图片。</span>
    </div>

    <div v-else class="ki-source-list ki-evidence-list">
      <button
        v-for="source in sources"
        :key="source.source_path"
        class="ki-source-item"
        :class="{ 'is-active': source.source_path === selectedSource?.source_path }"
        type="button"
        @click="openMaterial(source)"
      >
        <span class="ki-source-index">{{ source.evidence_ids.join("、") || "资料" }}</span>
        <strong>{{ source.title }}</strong>
        <small>{{ formatScore(source.score) }}</small>
      </button>
    </div>
  </section>

</template>

<script setup lang="ts">
import type { SourceSnippet } from "../api/types";

defineProps<{
  sources: SourceSnippet[];
  selectedSource: SourceSnippet | null;
}>();

const emit = defineEmits<{
  openMaterial: [source: SourceSnippet];
}>();

// 通知顶层应用打开资料阅读器，避免弹窗被右侧资料栏的布局限制。
function openMaterial(source: SourceSnippet): void {
  emit("openMaterial", source);
}

// 格式化来源分数，后端没有返回分数时显示默认文案。
function formatScore(score: number | null): string {
  if (score === null) {
    return "无分数";
  }
  return `相似度 ${(score * 100).toFixed(0)}%`;
}
</script>
