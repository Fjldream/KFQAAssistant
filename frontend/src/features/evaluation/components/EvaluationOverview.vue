<template>
  <section class="ke-overview" aria-label="评测总览">
    <div class="ke-metric">
      <span>运行结果</span>
      <strong :class="outcomeClass">{{ outcomeLabel }}</strong>
      <small v-if="summary" data-testid="run-status">{{ summary.status.toUpperCase() }}</small>
    </div>
    <div class="ke-metric">
      <span>用例通过率</span>
      <strong>{{ formatPercent(summary?.pass_rate ?? 0) }}</strong>
    </div>
    <div class="ke-metric">
      <span>P0</span>
      <strong>{{ summary?.p0_passed ?? 0 }}/{{ summary?.p0_total ?? 0 }}</strong>
    </div>
    <div class="ke-metric">
      <span>P95</span>
      <strong>{{ formatMs(summary?.p95_latency_ms ?? 0) }}</strong>
    </div>
    <div class="ke-metric">
      <span>平均忠实度</span>
      <strong>{{ avgFaithfulness === null ? "未评估" : formatPercent(avgFaithfulness) }}</strong>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { EvaluationRunDetail } from "../types";

const props = defineProps<{
  detail: EvaluationRunDetail | null;
}>();

const summary = computed(() => props.detail?.summary ?? null);
const avgFaithfulness = computed(() => summary.value?.avg_faithfulness_score ?? null);
const outcomeLabel = computed(() => {
  if (summary.value?.status === "INVALID") return "无效";
  if (!props.detail) return "未开始";
  return props.detail.gate_result.passed ? "通过" : "质量未通过";
});
const outcomeClass = computed(() => summary.value?.status === "INVALID" ? "is-invalid" : props.detail?.gate_result.passed ? "is-pass" : "is-fail");

// 将小数通过率格式化成百分比文本。
function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

// 将毫秒耗时格式化成紧凑文本。
function formatMs(value: number): string {
  return `${Math.round(value)}ms`;
}
</script>
