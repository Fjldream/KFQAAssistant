<template>
  <section class="ki-evidence-panel">
    <header>
      <p class="ki-section-title">证据与图片</p>
      <h2>来源依据</h2>
    </header>

    <div v-if="sources.length === 0" class="ki-empty-block">
      <p>暂无来源</p>
      <span>提问后会显示手册片段、路径和相关图片。</span>
    </div>

    <div v-else class="ki-source-list">
      <button
        v-for="source in sources"
        :key="source.source_path"
        class="ki-source-item"
        :class="{ 'is-active': source.source_path === selectedSource?.source_path }"
        type="button"
        @click="emit('selectSource', source)"
      >
        <strong>{{ source.title }}</strong>
        <span>{{ source.evidence_ids.join("、") || "资料" }}</span>
        <small>{{ formatScore(source.score) }}</small>
      </button>
    </div>

    <article v-if="selectedSource" class="ki-source-detail">
      <p class="ki-path-text">{{ selectedSource.source_path }}</p>
      <p>{{ selectedSource.snippet }}</p>
      <div v-if="selectedSource.images.length" class="ki-image-grid">
        <button
          v-for="image in selectedSource.images"
          :key="image"
          class="ki-image-thumb"
          type="button"
          @click="emit('previewImage', image)"
        >
          <span>{{ image.split('/').pop() }}</span>
        </button>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { SourceSnippet } from "../api/types";

defineProps<{
  sources: SourceSnippet[];
  selectedSource: SourceSnippet | null;
}>();

const emit = defineEmits<{
  selectSource: [source: SourceSnippet];
  previewImage: [image: string];
}>();

// 格式化来源分数，后端没有返回分数时显示默认文案。
function formatScore(score: number | null): string {
  if (score === null) {
    return "无分数";
  }
  return `相似度 ${(score * 100).toFixed(0)}%`;
}
</script>
