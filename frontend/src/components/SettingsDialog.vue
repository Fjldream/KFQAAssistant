<template>
  <div v-if="open" class="ki-dialog-backdrop" role="presentation" @click.self="emit('close')">
    <section class="ki-dialog" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <header class="ki-dialog-header">
        <div>
          <p class="ki-section-title">连接设置</p>
          <h2 id="settings-title">API 配置</h2>
        </div>
        <button class="ki-icon-button" type="button" title="关闭" @click="emit('close')">
          <X :size="18" aria-hidden="true" />
        </button>
      </header>

      <label class="ki-field">
        <span>API Base URL</span>
        <input v-model="draftApiBaseUrl" type="url" placeholder="http://127.0.0.1:8000" />
      </label>

      <label class="ki-field">
        <span>API Key</span>
        <input v-model="draftApiKey" type="password" placeholder="本地免认证时可留空" />
      </label>

      <footer class="ki-dialog-actions">
        <button class="ki-secondary-button" type="button" @click="emit('reset')">重置</button>
        <button class="ki-primary-button" type="button" @click="save">保存</button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { X } from "lucide-vue-next";
import type { ApiSettings } from "../api/types";

const props = defineProps<{
  open: boolean;
  apiBaseUrl: string;
  apiKey: string;
}>();

const emit = defineEmits<{
  close: [];
  save: [settings: ApiSettings];
  reset: [];
}>();

const draftApiBaseUrl = ref(props.apiBaseUrl);
const draftApiKey = ref(props.apiKey);

watch(
  () => [props.apiBaseUrl, props.apiKey, props.open],
  () => {
    draftApiBaseUrl.value = props.apiBaseUrl;
    draftApiKey.value = props.apiKey;
  },
);

// 保存设置弹窗里的 API 配置。
function save(): void {
  emit("save", {
    apiBaseUrl: draftApiBaseUrl.value.trim(),
    apiKey: draftApiKey.value.trim(),
  });
}
</script>
