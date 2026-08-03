<template>
  <div
    v-if="source"
    class="ka-backdrop"
    role="presentation"
    @click.self="emit('close')"
  >
    <article
      class="ka-reader"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ka-material-title"
    >
      <header class="ka-reader__head">
        <div>
          <p class="ka-eyebrow">帮助手册资料</p>
          <h2 id="ka-material-title">{{ source.title }}</h2>
          <span class="ka-reader__index">{{ source.evidence_ids.join("、") || "资料" }}</span>
        </div>
        <button class="ka-icon-button" type="button" title="关闭资料" @click="emit('close')">
          <X :size="18" aria-hidden="true" />
        </button>
      </header>

      <div class="ka-reader__body">
        <section class="ka-reader__section">
          <p class="ka-reader__label">来源路径</p>
          <p class="ka-reader__path">{{ source.source_path }}</p>
        </section>

        <section class="ka-reader__section">
          <p class="ka-reader__label">命中段落</p>
          <p class="ka-reader__snippet">{{ source.snippet }}</p>
        </section>

        <section v-if="source.images.length" class="ka-reader__section">
          <p class="ka-reader__label">相关图片 · {{ source.images.length }}</p>
          <div class="ka-reader__images">
            <button
              v-for="image in source.images"
              :key="image"
              class="ka-thumb"
              type="button"
              :title="image.split('/').pop()"
              @click="emit('previewImage', imageUrl(image))"
            >
              <img :src="imageUrl(image)" :alt="image.split('/').pop()" loading="lazy" />
              <span class="ka-thumb__name">{{ image.split('/').pop() }}</span>
            </button>
          </div>
        </section>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, watch } from "vue";
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

// 监听 Escape 键，方便用户快速关闭资料阅读器。
function handleKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    emit("close");
  }
}

watch(
  () => props.source,
  (source) => {
    if (source) {
      window.addEventListener("keydown", handleKeydown);
    } else {
      window.removeEventListener("keydown", handleKeydown);
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown);
});

// 将资料图片路径转换为浏览器可访问的后端静态资源地址。
function imageUrl(image: string): string {
  return resolveImageUrl(props.apiBaseUrl, image);
}
</script>
