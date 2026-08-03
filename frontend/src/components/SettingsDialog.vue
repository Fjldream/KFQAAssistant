<template>
  <div v-if="open" class="ka-backdrop" role="presentation" @click.self="emit('close')">
    <section class="ka-dialog" role="dialog" aria-modal="true" aria-labelledby="ka-settings-title">
      <header class="ka-dialog__head">
        <div>
          <p class="ka-eyebrow">连接与外观</p>
          <h2 id="ka-settings-title">设置</h2>
        </div>
        <button class="ka-icon-button" type="button" title="关闭" @click="emit('close')">
          <X :size="18" aria-hidden="true" />
        </button>
      </header>

      <label class="ka-field">
        <span class="ka-field__label">外观</span>
        <div class="ka-segmented" role="radiogroup" aria-label="外观">
          <button
            v-for="option in themeOptions"
            :key="option.value"
            type="button"
            role="radio"
            :aria-checked="themePreference === option.value"
            :class="{ 'is-active': themePreference === option.value }"
            @click="emit('themeChange', option.value)"
          >
            <component :is="option.icon" :size="15" aria-hidden="true" />
            {{ option.label }}
          </button>
        </div>
      </label>

      <label class="ka-field">
        <span class="ka-field__label">API Base URL</span>
        <input v-model="draftApiBaseUrl" type="url" placeholder="http://127.0.0.1:8000" />
        <span class="ka-field__hint">RAG 后端服务地址，保存后立即生效。</span>
      </label>

      <label class="ka-field">
        <span class="ka-field__label">API Key</span>
        <input v-model="draftApiKey" type="password" placeholder="本地免认证时可留空" autocomplete="off" />
        <span class="ka-field__hint">生产环境需要填写后端配置的 APP_API_KEY。</span>
      </label>

      <footer class="ka-dialog__actions">
        <button class="ka-button ka-button--ghost" type="button" @click="emit('reset')">重置</button>
        <button class="ka-button ka-button--primary" type="button" @click="save">保存</button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { Monitor, Moon, Sun, X } from "lucide-vue-next";
import type { ApiSettings, ThemePreference } from "../api/types";

const props = defineProps<{
  open: boolean;
  apiBaseUrl: string;
  apiKey: string;
  themePreference: ThemePreference;
}>();

const emit = defineEmits<{
  close: [];
  save: [settings: ApiSettings];
  reset: [];
  themeChange: [preference: ThemePreference];
}>();

const themeOptions = computed(() => [
  { value: "light" as const, label: "浅色", icon: Sun },
  { value: "dark" as const, label: "深色", icon: Moon },
  { value: "system" as const, label: "跟随系统", icon: Monitor },
]);

const draftApiBaseUrl = ref(props.apiBaseUrl);
const draftApiKey = ref(props.apiKey);

watch(
  () => [props.apiBaseUrl, props.apiKey, props.open],
  () => {
    draftApiBaseUrl.value = props.apiBaseUrl;
    draftApiKey.value = props.apiKey;
  },
);

// 监听 Escape 键关闭设置弹窗。
function handleKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") {
    emit("close");
  }
}

watch(
  () => props.open,
  (open) => {
    if (open) {
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

// 保存设置弹窗里的 API 配置。
function save(): void {
  emit("save", {
    apiBaseUrl: draftApiBaseUrl.value.trim(),
    apiKey: draftApiKey.value.trim(),
  });
}
</script>
