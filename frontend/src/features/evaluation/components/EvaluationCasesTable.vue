<template>
  <section class="ke-panel">
    <div class="ke-panel__head">
      <h3>用例列表</h3>
      <span>{{ cases.length }} 条</span>
    </div>
    <div class="ke-table">
      <button v-for="item in cases" :key="item.id" class="ke-row" type="button">
        <span class="ke-row__main">
          <strong>{{ item.id }}</strong>
          <small>{{ item.turns[0]?.question }}</small>
        </span>
        <span class="ke-badge">{{ item.priority }}</span>
        <span class="ke-type">{{ item.case_type === "dialogue" ? "连续对话" : "单轮" }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { EvaluationCase } from "../types";

defineProps<{
  cases: EvaluationCase[];
}>();
</script>
