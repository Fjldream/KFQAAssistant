<template>
  <section class="ke-compare">
    <div>
      <span>相邻对比</span>
      <strong>{{ formatDelta(comparison?.pass_rate_delta ?? 0) }}</strong>
    </div>
    <div>
      <span>新增失败</span>
      <strong>{{ comparison?.regressed_case_ids?.length ?? 0 }}</strong>
    </div>
    <div>
      <span>恢复通过</span>
      <strong>{{ comparison?.recovered_case_ids?.length ?? 0 }}</strong>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { ComparisonResult } from "../types";

defineProps<{
  comparison: ComparisonResult | null;
}>();

// 将通过率变化格式化成带正负号的百分比。
function formatDelta(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${Math.round(value * 100)}%`;
}
</script>
