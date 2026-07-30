<template>
  <section class="ki-evidence-panel">
    <header>
      <p class="ki-section-title">资料与图片</p>
      <h2>资料中心</h2>
      <span>{{ sources.length }} 个资料片段</span>
    </header>

    <div v-if="sources.length === 0" class="ki-empty-block">
      <p>暂无资料</p>
      <span>提问后会显示手册段落、路径和相关图片。</span>
    </div>

    <div v-else class="ki-source-list">
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

  <div v-if="activeMaterial" class="ki-material-backdrop" role="presentation" @click.self="closeMaterial">
    <article class="ki-material-dialog" role="dialog" aria-modal="true" aria-labelledby="material-title">
      <header class="ki-material-header">
        <div>
          <p class="ki-section-title">帮助手册资料</p>
          <h2 id="material-title">{{ activeMaterial.title }}</h2>
          <span class="ki-source-index">{{ activeMaterial.evidence_ids.join("、") || "资料" }}</span>
        </div>
        <button class="ki-icon-button" type="button" title="关闭资料" @click="closeMaterial">
          <X :size="18" aria-hidden="true" />
        </button>
      </header>

      <div class="ki-material-body">
        <section class="ki-material-section">
          <p class="ki-material-label">来源路径</p>
          <p class="ki-path-text">{{ activeMaterial.source_path }}</p>
        </section>

        <section class="ki-material-section">
          <p class="ki-material-label">命中段落</p>
          <div class="ki-material-paragraph">{{ activeMaterial.snippet }}</div>
        </section>

        <section v-if="activeMaterial.images.length" class="ki-material-section">
          <p class="ki-material-label">相关图片</p>
          <div class="ki-material-image-grid">
            <button
              v-for="image in activeMaterial.images"
              :key="image"
              class="ki-image-thumb"
              type="button"
              @click="emit('previewImage', imageUrl(image))"
            >
              <span>{{ image.split('/').pop() }}</span>
            </button>
          </div>
        </section>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { X } from "lucide-vue-next";
import { resolveImageUrl } from "../api/client";
import type { SourceSnippet } from "../api/types";

const props = defineProps<{
  sources: SourceSnippet[];
  selectedSource: SourceSnippet | null;
  apiBaseUrl: string;
}>();

const emit = defineEmits<{
  selectSource: [source: SourceSnippet];
  previewImage: [image: string];
}>();

const activeMaterial = ref<SourceSnippet | null>(null);

// 打开资料阅读弹窗，并同步选中右侧资料条目。
function openMaterial(source: SourceSnippet): void {
  activeMaterial.value = source;
  emit("selectSource", source);
}

// 关闭资料阅读弹窗，保留右侧当前选中资料状态。
function closeMaterial(): void {
  activeMaterial.value = null;
}

// 格式化来源分数，后端没有返回分数时显示默认文案。
function formatScore(score: number | null): string {
  if (score === null) {
    return "无分数";
  }
  return `相似度 ${(score * 100).toFixed(0)}%`;
}

// 将来源图片路径转换为浏览器可访问地址。
function imageUrl(image: string): string {
  return resolveImageUrl(props.apiBaseUrl, image);
}
</script>
