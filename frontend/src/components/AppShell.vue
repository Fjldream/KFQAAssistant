<template>
  <div class="ka-app" :class="{ 'ka-app--evidence-hidden': !evidenceOpen }">
    <aside id="ka-sidebar" class="ka-app__sidebar" :class="{ 'is-open': sidebarOpen }" aria-label="知识导航">
      <slot name="sidebar"></slot>
    </aside>

    <main class="ka-app__main" aria-label="问答工作区">
      <div class="ka-topbar">
        <span class="ka-topbar__title">KingIAsk</span>
        <nav class="ka-topbar__nav" aria-label="主导航">
          <button
            class="ka-topbar__tab"
            :class="{ 'is-active': activeView === 'chat' }"
            type="button"
            @click="emit('viewChange', 'chat')"
          >
            问答助手
          </button>
          <button
            class="ka-topbar__tab"
            :class="{ 'is-active': activeView === 'evaluation' }"
            type="button"
            @click="emit('viewChange', 'evaluation')"
          >
            评测中心
          </button>
        </nav>
        <div class="ka-topbar__actions">
          <button
            class="ka-icon-button ka-mobile-menu"
            type="button"
            title="打开导航"
            :aria-expanded="sidebarOpen"
            aria-controls="ka-sidebar"
            @click="toggleSidebar"
          >
            <Menu :size="18" aria-hidden="true" />
          </button>
        </div>
      </div>
      <slot></slot>
    </main>

    <aside v-if="evidenceOpen" class="ka-app__evidence" aria-label="资料与图片">
      <slot name="evidence"></slot>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Menu } from "lucide-vue-next";

defineProps<{
  evidenceOpen: boolean;
  activeView?: "chat" | "evaluation";
}>();

const emit = defineEmits<{
  viewChange: [view: "chat" | "evaluation"];
}>();

const sidebarOpen = ref(false);

// 切换移动端侧边栏显示状态。
function toggleSidebar(): void {
  sidebarOpen.value = !sidebarOpen.value;
}
</script>
