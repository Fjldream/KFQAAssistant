<template>
  <section class="ka-evidence">
    <header class="ka-evidence__head">
      <div>
        <p class="ka-eyebrow">资料与图片</p>
        <h2>资料中心</h2>
        <p class="ka-evidence__count">{{ sources.length }} 个资料片段</p>
      </div>
      <button
        class="ka-icon-button ka-evidence__collapse"
        type="button"
        title="收起资料中心"
        aria-label="收起资料中心"
        @click="emit('collapse')"
      >
        <ChevronsRight :size="18" aria-hidden="true" />
      </button>
    </header>

    <div v-if="sources.length === 0" class="ka-evidence__empty">
      <div>
        <p>暂无资料</p>
        <span>提问后会显示手册段落、来源路径、相似度和相关图片。</span>
      </div>
    </div>

    <div v-else class="ka-evidence__list" data-testid="evidence-list">
      <button
        v-for="source in sources"
        :key="source.source_path"
        class="ka-source"
        :class="{ 'is-active': source.source_path === selectedSource?.source_path }"
        type="button"
        data-testid="source-item"
        @click="openMaterial(source)"
      >
        <div class="ka-source__top">
          <span class="ka-source__index">{{ source.evidence_ids.join("、") || "资" }}</span>
          <span class="ka-source__title" :title="source.title">{{ source.title }}</span>
        </div>
        <p class="ka-source__snippet">{{ source.snippet }}</p>
        <div class="ka-source__foot">
          <span class="ka-score">
            <span class="ka-score__bar">
              <span class="ka-score__fill" :style="{ width: scorePercent(source.score) }"></span>
            </span>
            <span class="ka-score__value">{{ scorePercent(source.score) }}</span>
          </span>
          <ChevronRight :size="15" class="ka-source__chevron" aria-hidden="true" />
        </div>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ChevronRight, ChevronsRight } from "lucide-vue-next";
import type { SourceSnippet } from "../api/types";

defineProps<{
  sources: SourceSnippet[];
  selectedSource: SourceSnippet | null;
}>();

const emit = defineEmits<{
  openMaterial: [source: SourceSnippet];
  collapse: [];
}>();

// 通知顶层应用打开资料阅读器，避免弹窗被右侧资料栏的布局限制。
function openMaterial(source: SourceSnippet): void {
  emit("openMaterial", source);
}

// 把相似度分数格式化为百分比；后端未返回时显示占位。
function scorePercent(score: number | null): string {
  if (score === null) {
    return "—";
  }
  return `${Math.round(score * 100)}%`;
}
</script>
