<template>
  <div v-if="image" class="ki-preview-backdrop" role="presentation" @click.self="emit('close')">
    <figure class="ki-preview">
      <button class="ki-icon-button" type="button" title="关闭" @click="emit('close')">
        <X :size="18" aria-hidden="true" />
      </button>
      <img v-if="!loadFailed" :src="image" :alt="image" @error="loadFailed = true" />
      <figcaption v-else>图片暂不可预览：{{ image }}</figcaption>
    </figure>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, watch, ref } from "vue";
import { X } from "lucide-vue-next";

const props = defineProps<{
  image: string | null;
}>();

const emit = defineEmits<{
  close: [];
}>();

const loadFailed = ref(false);

// 监听 Escape 键，方便用户快速关闭图片预览。
function handleKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    emit("close");
  }
}

watch(
  () => props.image,
  (image) => {
    loadFailed.value = false;
    if (image) {
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
</script>
