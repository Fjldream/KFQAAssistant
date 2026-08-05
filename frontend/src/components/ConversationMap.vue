<template>
  <nav v-if="rounds.length > 1" class="ka-map" aria-label="对话轮次导航" data-testid="conversation-map">
    <button
      v-for="(round, index) in rounds"
      :key="round.userIndex"
      class="ka-map__dot"
      :class="{ 'is-active': round.userIndex === activeUserIndex }"
      type="button"
      :aria-label="`跳转到第 ${index + 1} 轮对话`"
      @click="emit('jump', round.userIndex)"
    >
      <span class="ka-map__tip" role="tooltip">
        <strong>{{ round.question }}</strong>
        <span v-if="round.answer">{{ round.answer }}</span>
        <em v-else>等待回答…</em>
      </span>
    </button>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ChatMessage } from "../api/types";

interface ConversationRound {
  question: string;
  answer: string;
  userIndex: number;
}

const props = defineProps<{
  messages: ChatMessage[];
  /** 当前正在查看的轮次（用户消息下标），用于高亮对应方块。 */
  activeUserIndex?: number | null;
}>();

const emit = defineEmits<{
  jump: [userIndex: number];
}>();

// 把消息序列配对为轮次：每条 user 消息开启一轮，下一条 assistant 消息作为该轮回答。
const rounds = computed<ConversationRound[]>(() => {
  const result: ConversationRound[] = [];
  let current: ConversationRound | null = null;
  props.messages.forEach((message, index) => {
    if (message.role === "user") {
      current = { question: message.content, answer: "", userIndex: index };
      result.push(current);
    } else if (message.role === "assistant" && current) {
      current.answer = message.content;
    }
  });
  return result;
});
</script>
