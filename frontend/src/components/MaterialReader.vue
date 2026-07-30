<template>
  <div v-if="source" class="ki-material-backdrop" role="presentation" @click.self="emit('close')">
    <article class="ki-material-dialog ki-material-dialog--page" role="dialog" aria-modal="true" aria-labelledby="material-title">
      <header class="ki-material-header">
        <div>
          <p class="ki-section-title">帮助手册资料</p>
          <h2 id="material-title">{{ source.title }}</h2>
          <span class="ki-source-index">{{ source.evidence_ids.join("、") || "资料" }}</span>
        </div>
        <button class="ki-icon-button" type="button" title="关闭资料" @click="emit('close')">
          <X :size="18" aria-hidden="true" />
        </button>
      </header>

      <div class="ki-material-body">
        <section class="ki-material-section">
          <p class="ki-material-label">来源路径</p>
          <p class="ki-path-text">{{ source.source_path }}</p>
        </section>

        <section class="ki-material-section ki-material-section--main">
          <p class="ki-material-label">命中段落</p>
          <div class="ki-material-paragraph">{{ source.snippet }}</div>
        </section>

        <section v-if="source.images.length" class="ki-material-section">
          <p class="ki-material-label">相关图片</p>
          <div class="ki-material-image-grid">
            <button
              v-for="image in source.images"
              :key="image"
              class="ki-image-thumb"
              type="button"
              @click="emit('previewImage', imageUrl(image))"
            >
              <img :src="imageUrl(image)" :alt="image.split('/').pop()" />
              <span>{{ image.split('/').pop() }}</span>
            </button>
          </div>
        </section>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { X } from "lucide-vue-next";
import { resolveImageUrl } from "../api/client";
import type { SourceSnippet } from "../api/types";

const props = defineProps<{
  source: SourceSnippet | null;
  apiBaseUrl: string;
}>();

const emit = defineEmits<{
  close: [];
  previewImage: [image: string];
}>();

// 将资料图片路径转换为浏览器可访问的后端静态资源地址。
function imageUrl(image: string): string {
  return resolveImageUrl(props.apiBaseUrl, image);
}
</script>
