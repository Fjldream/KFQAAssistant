<template>
  <img class="ka-logo" :src="LOGO_URL" :width="size" :height="size" alt="KingIAsk 标志" />
</template>

<script setup lang="ts">
// 企业 OEM 标志：由运营平台提供，替换默认的图形 LOGO。
const LOGO_URL = "https://192.168.3.32/opscenter/oemImg/leftIcon.png";

withDefaults(
  defineProps<{
    size?: number;
  }>(),
  { size: 32 },
);
</script>
