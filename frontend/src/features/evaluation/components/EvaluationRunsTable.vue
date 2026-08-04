<template>
  <section class="ke-panel">
    <div class="ke-panel__head">
      <h3>运行历史</h3>
      <span>{{ runs.length }} 次</span>
    </div>
    <div class="ke-table">
      <button
        v-for="run in runs"
        :key="run.run_id"
        class="ke-row"
        :class="{ 'is-active': run.run_id === selectedRunId }"
        type="button"
        @click="emit('select', run.run_id)"
      >
        <span class="ke-row__main">
          <strong>{{ run.run_id }}</strong>
          <small>{{ run.status }} · {{ run.case_passed }}/{{ run.case_total }}</small>
        </span>
        <span class="ke-badge" :class="run.pass_rate >= 0.8 ? 'is-pass' : 'is-fail'">
          {{ formatPercent(run.pass_rate) }}
        </span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { EvaluationRunSummary } from "../types";

defineProps<{
  runs: EvaluationRunSummary[];
  selectedRunId: string | null;
}>();

const emit = defineEmits<{
  select: [runId: string];
}>();

// 将通过率格式化成百分比，便于历史列表快速扫描。
function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
</script>
