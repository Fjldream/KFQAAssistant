<template>
  <section class="ke-detail">
    <div class="ke-panel__head">
      <h3>报告详情</h3>
      <span v-if="detail">{{ detail.summary.run_id }}</span>
    </div>
    <div v-if="!detail" class="ke-empty">暂无评测报告</div>
    <div v-else class="ke-result-list">
      <article
        v-for="item in detail.case_results"
        :key="item.case_id"
        class="ke-result"
        :class="item.passed ? 'is-pass' : 'is-fail'"
      >
        <header>
          <div>
            <strong>{{ item.case_id }}</strong>
            <small>{{ item.category }} · {{ item.priority }} · {{ item.case_type }}</small>
          </div>
          <span>{{ item.passed ? "通过" : "失败" }}</span>
        </header>
        <p v-for="reason in item.failure_reasons" :key="reason" class="ke-reason">{{ reason }}</p>
        <ul v-if="item.metric_results.length" class="ke-metrics">
          <li v-for="metric in item.metric_results" :key="metric.name" :class="metric.status === 'ERROR' ? 'ke-metric-error' : ''">
            {{ metricGroup(metric.name) }} · {{ metric.name }}：{{ metric.status === "ERROR" ? `错误${metric.error_code ? ` (${metric.error_code})` : ""}` : metric.status }}
          </li>
        </ul>
        <details v-for="(turn, index) in item.turn_results" :key="`${item.case_id}-${index}`">
          <summary>第 {{ index + 1 }} 轮：{{ turn.question }}</summary>
          <div class="ke-turn">
            <p>{{ turn.answer }}</p>
            <small v-if="turn.standalone_question">独立问题：{{ turn.standalone_question }}</small>
            <p
              v-if="turn.faithfulness_score !== null && turn.faithfulness_score !== undefined"
              class="ke-faithfulness"
            >
              忠实度：{{ Math.round(turn.faithfulness_score * 100) }}%
            </p>
            <p v-else class="ke-faithfulness">忠实度：未评估</p>
            <ul v-if="turn.faithfulness_claims && turn.faithfulness_claims.length" class="ke-claims">
              <li
                v-for="(claim, i) in turn.faithfulness_claims.filter((c) => !c.supported)"
                :key="i"
                class="ke-claim-hallucination"
              >
                幻觉句：{{ claim.claim }}（{{ claim.evidence || "上下文中无依据" }}）
              </li>
            </ul>
          </div>
        </details>
      </article>
    </div>
    <details v-if="detail?.snapshot" class="ke-snapshot"><summary>运行快照与基准标识</summary><pre>{{ JSON.stringify(detail.snapshot, null, 2) }}</pre></details>
  </section>
</template>

<script setup lang="ts">
import type { EvaluationRunDetail } from "../types";

defineProps<{
  detail: EvaluationRunDetail | null;
}>();

function metricGroup(name: string): string {
  if (["keyword", "source", "image", "no_answer", "required_fact_coverage"].some((part) => name.includes(part))) return "硬规则";
  if (["faithfulness"].some((part) => name.includes(part))) return "忠实度";
  if (["retrieval", "hit_at_k", "mrr", "recall"].some((part) => name.includes(part))) return "检索";
  if (["latency", "token", "cost"].some((part) => name.includes(part))) return "系统";
  return "答案质量";
}
</script>

<style scoped>
.ke-claim-hallucination {
  color: var(--ka-red, red);
}
.ke-metric-error { color: var(--ka-red, red); }
.ke-snapshot { padding: 12px 6px; }
.ke-snapshot pre { overflow: auto; white-space: pre-wrap; }
</style>
