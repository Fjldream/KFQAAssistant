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
  </section>
</template>

<script setup lang="ts">
import type { EvaluationRunDetail } from "../types";

defineProps<{
  detail: EvaluationRunDetail | null;
}>();
</script>

<style scoped>
.ke-claim-hallucination {
  color: var(--ka-red, red);
}
</style>
