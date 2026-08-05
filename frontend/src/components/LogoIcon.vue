<template>
  <img class="ka-logo" :src="LOGO_URL" :width="size" :height="size" alt="KingIAsk 标志" />
</template>

<script setup lang="ts">
// 品牌 LOGO：本地静态图片（OEM 图标），用相对路径避免内网地址与证书问题。
const LOGO_URL = "/logo.png";

withDefaults(
  defineProps<{
    size?: number;
  }>(),
  { size: 32 },
);
</script>
