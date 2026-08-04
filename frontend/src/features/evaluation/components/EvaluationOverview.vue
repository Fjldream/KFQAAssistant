<template>
  <section class="ke-overview" aria-label="评测总览">
    <div class="ke-metric">
      <span>通过率</span>
      <strong>{{ formatPercent(summary?.pass_rate ?? 0) }}</strong>
    </div>
    <div class="ke-metric">
      <span>用例</span>
      <strong>{{ summary?.case_passed ?? 0 }}/{{ summary?.case_total ?? 0 }}</strong>
    </div>
    <div class="ke-metric">
      <span>P0</span>
      <strong>{{ summary?.p0_passed ?? 0 }}/{{ summary?.p0_total ?? 0 }}</strong>
    </div>
    <div class="ke-metric">
      <span>P95</span>
      <strong>{{ formatMs(summary?.p95_latency_ms ?? 0) }}</strong>
    </div>
    <div class="ke-gate" :class="gatePassed ? 'is-pass' : 'is-fail'">
      <span>门禁</span>
      <strong>{{ gatePassed ? "通过" : "未通过" }}</strong>
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
const gatePassed = computed(() => props.detail?.gate_result.passed ?? false);

// 将小数通过率格式化成百分比文本。
function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

// 将毫秒耗时格式化成紧凑文本。
function formatMs(value: number): string {
  return `${Math.round(value)}ms`;
}
</script>
