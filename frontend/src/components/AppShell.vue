<template>
  <div class="ki-layout">
    <aside class="ki-layout__sidebar" :class="{ 'is-open': sidebarOpen }" aria-label="知识导航">
      <slot name="sidebar"></slot>
    </aside>

    <main class="ki-layout__main" aria-label="问答工作区">
      <button class="ki-icon-button ki-mobile-menu" type="button" title="打开导航" @click="toggleSidebar">
        <Menu :size="18" aria-hidden="true" />
      </button>
      <slot></slot>
    </main>

    <aside class="ki-layout__evidence" aria-label="证据与图片">
      <slot name="evidence"></slot>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Menu } from "lucide-vue-next";

const sidebarOpen = ref(false);

// 切换移动端侧边栏显示状态。
function toggleSidebar(): void {
  sidebarOpen.value = !sidebarOpen.value;
}
</script>
