<template>
  <section class="ke-detail">
    <div class="ke-panel__head">
      <h3>报告详情</h3>
      <span v-if="detail">{{ detail.summary.run_id }}</span>
    </div>

    <div v-if="!detail" class="ke-empty">暂无评测报告</div>
    <div v-else class="ke-diagnostic-shell">
      <aside class="ke-question-pane" data-testid="evaluation-question-list">
        <button
          v-for="item in questionItems"
          :key="item.id"
          type="button"
          class="ke-question-item"
          :class="[{ 'is-active': item.id === selectedId }, item.passed ? 'is-pass' : 'is-fail']"
          data-testid="evaluation-question-item"
          @click="selectedId = item.id"
        >
          <span class="ke-state-dot" aria-hidden="true"></span>
          <span class="ke-question-main">
            <strong>{{ item.question }}</strong>
            <small>{{ item.caseId }}</small>
            <em v-if="item.failureSummary">{{ item.failureSummary }}</em>
          </span>
          <span class="ke-question-meta">
            <b>{{ item.priority }}</b>
            <i>{{ item.category }}</i>
            <small v-if="item.turnTotal > 1">{{ item.turnTotal }} 轮</small>
          </span>
        </button>
      </aside>

      <article v-if="selectedItem" class="ke-diagnostic-pane">
        <header class="ke-diagnostic-head">
          <div>
            <span :class="selectedItem.passed ? 'is-pass' : 'is-fail'">{{ selectedItem.passed ? "通过" : "失败" }}</span>
            <h4 data-testid="selected-question">{{ selectedItem.question }}</h4>
            <p>{{ selectedItem.caseId }} · {{ selectedItem.category }} · {{ selectedItem.priority }} · 第 {{ selectedItem.turnIndex + 1 }} 轮</p>
          </div>
          <strong v-if="selectedItem.turn.elapsed_ms">{{ Math.round(selectedItem.turn.elapsed_ms) }}ms</strong>
        </header>

        <section v-if="selectedItem.failures.length" class="ke-diagnostic-section">
          <h5>失败原因</h5>
          <ul class="ke-reason-list">
            <li v-for="reason in selectedItem.failures" :key="reason">{{ reason }}</li>
          </ul>
        </section>

        <section class="ke-diagnostic-section">
          <h5>RAG 回答</h5>
          <p v-if="selectedItem.turn.standalone_question" class="ke-muted-line">
            独立问题：{{ selectedItem.turn.standalone_question }}
          </p>
          <pre class="ke-answer-block" data-testid="selected-rag-answer">{{ selectedItem.turn.answer || "无回答" }}</pre>
        </section>

        <section class="ke-diagnostic-section">
          <h5>规则检查</h5>
          <div class="ke-rule-grid">
            <span :class="ruleClass(selectedItem.turn.keyword_passed)">关键词</span>
            <span :class="ruleClass(selectedItem.turn.source_passed)">来源</span>
            <span :class="ruleClass(selectedItem.turn.image_passed)">图片</span>
            <span :class="ruleClass(selectedItem.turn.no_answer_passed)">拒答</span>
          </div>
          <p v-if="selectedItem.turn.missing_keywords?.length" class="ke-muted-line">
            缺少关键词：{{ selectedItem.turn.missing_keywords.join("、") }}
          </p>
          <p v-if="selectedItem.turn.missing_source_keywords?.length" class="ke-muted-line">
            缺少来源关键词：{{ selectedItem.turn.missing_source_keywords.join("、") }}
          </p>
          <p v-if="selectedItem.turn.forbidden_source_matches?.length" class="ke-muted-line">
            命中禁止来源：{{ selectedItem.turn.forbidden_source_matches.join("、") }}
          </p>
        </section>

        <section class="ke-diagnostic-section" data-testid="selected-metrics">
          <h5>评测指标</h5>
          <div v-if="selectedItem.turn.metric_results.length" class="ke-metric-list">
            <div
              v-for="metric in selectedItem.turn.metric_results"
              :key="metric.name"
              class="ke-metric-row"
              :class="metric.status === 'FAILED' || metric.status === 'ERROR' ? 'is-fail' : metric.status === 'PASSED' ? 'is-pass' : ''"
            >
              <span>{{ metricGroup(metric.name) }}</span>
              <strong>{{ metric.name }}</strong>
              <small>
                {{ metric.status }}
                <template v-if="metric.score !== null && metric.score !== undefined"> · {{ formatScore(metric.score) }}</template>
                <template v-if="metric.threshold !== null && metric.threshold !== undefined"> / {{ formatScore(metric.threshold) }}</template>
                <template v-if="metric.error_code"> · {{ metric.error_code }}</template>
              </small>
            </div>
          </div>
          <p v-else class="ke-muted-line">无指标明细</p>
        </section>

        <section class="ke-diagnostic-section">
          <h5>忠实度</h5>
          <p class="ke-muted-line">
            {{ selectedItem.turn.faithfulness_score === null || selectedItem.turn.faithfulness_score === undefined
              ? "未评估"
              : `${Math.round(selectedItem.turn.faithfulness_score * 100)}%` }}
          </p>
          <ul v-if="unsupportedClaims.length" class="ke-claim-list">
            <li v-for="(claim, index) in unsupportedClaims" :key="index">
              <strong>未支持：</strong>{{ claim.claim }}
              <small>{{ claim.evidence || "上下文中无依据" }}</small>
            </li>
          </ul>
        </section>

        <section class="ke-diagnostic-section" data-testid="selected-sources">
          <h5>检索来源</h5>
          <div v-if="selectedSources.length" class="ke-source-list">
            <article v-for="(source, index) in selectedSources" :key="`${source.source_path || source.title}-${index}`">
              <div>
                <strong>{{ source.title || `资料 ${index + 1}` }}</strong>
                <small v-if="source.score !== null && source.score !== undefined">score {{ source.score.toFixed(3) }}</small>
              </div>
              <p v-if="source.source_path">{{ source.source_path }}</p>
              <blockquote v-if="source.snippet">{{ source.snippet }}</blockquote>
              <small v-if="source.images?.length">图片 {{ source.images.length }} 张</small>
            </article>
          </div>
          <p v-else class="ke-muted-line">没有返回来源</p>
        </section>
      </article>
    </div>

    <details v-if="detail?.snapshot" class="ke-snapshot">
      <summary>运行快照与基准标识</summary>
      <pre>{{ JSON.stringify(detail.snapshot, null, 2) }}</pre>
    </details>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { CaseResult, EvaluationRunDetail, MetricResult, TurnResult } from "../types";

const props = defineProps<{
  detail: EvaluationRunDetail | null;
}>();

interface QuestionItem {
  id: string;
  caseId: string;
  category: string;
  priority: string;
  passed: boolean;
  question: string;
  failureSummary: string;
  failures: string[];
  turn: TurnResult;
  turnIndex: number;
  turnTotal: number;
}

const selectedId = ref("");

const questionItems = computed<QuestionItem[]>(() => {
  if (!props.detail) return [];
  return props.detail.case_results.flatMap((result: CaseResult) =>
    result.turn_results.map((turn, turnIndex) => ({
      id: `${result.case_id}:${turnIndex}`,
      caseId: result.case_id,
      category: result.category,
      priority: result.priority,
      passed: turn.passed && result.passed,
      question: turn.question,
      failureSummary: summarizeFailures(result.failure_reasons, turn.metric_results),
      failures: result.failure_reasons,
      turn,
      turnIndex,
      turnTotal: result.turn_results.length,
    })),
  );
});

const selectedItem = computed(() =>
  questionItems.value.find((item) => item.id === selectedId.value) ?? questionItems.value[0] ?? null,
);

const selectedSources = computed(() => selectedItem.value?.turn.sources ?? []);
const unsupportedClaims = computed(() =>
  selectedItem.value?.turn.faithfulness_claims?.filter((claim) => !claim.supported) ?? [],
);

watch(questionItems, (items) => {
  if (!items.some((item) => item.id === selectedId.value)) {
    selectedId.value = items[0]?.id ?? "";
  }
}, { immediate: true });

function summarizeFailures(reasons: string[], metrics: MetricResult[]): string {
  if (reasons.length) return reasons[0];
  const failedMetric = metrics.find((metric) => metric.status === "FAILED" || metric.status === "ERROR");
  return failedMetric ? `${failedMetric.name} ${failedMetric.status}` : "";
}

function metricGroup(name: string): string {
  if (["keyword", "source", "image", "no_answer", "required_fact_coverage"].some((part) => name.includes(part))) return "硬规则";
  if (["faithfulness"].some((part) => name.includes(part))) return "忠实度";
  if (["retrieval", "hit_at_k", "mrr", "recall"].some((part) => name.includes(part))) return "检索";
  if (["latency", "token", "cost"].some((part) => name.includes(part))) return "系统";
  return "答案质量";
}

function formatScore(value: number): string {
  if (value >= 0 && value <= 1) return `${Math.round(value * 100)}%`;
  return String(Math.round(value * 100) / 100);
}

function ruleClass(value: boolean | undefined): string {
  if (value === true) return "is-pass";
  if (value === false) return "is-fail";
  return "is-skip";
}
</script>

<style scoped>
.ke-diagnostic-shell {
  display: grid;
  height: calc(100% - 46px);
  min-height: 520px;
  grid-template-columns: minmax(260px, 0.9fr) minmax(0, 1.6fr);
  overflow: hidden;
}

.ke-question-pane {
  overflow: auto;
  border-right: 1px solid color-mix(in srgb, var(--ka-border) 80%, transparent);
  background: color-mix(in srgb, var(--ka-surface-muted) 46%, transparent);
  padding: 10px;
}

.ke-question-item {
  display: grid;
  width: 100%;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  align-items: start;
  gap: 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--ka-text-primary);
  cursor: pointer;
  padding: 10px;
  text-align: left;
  transition: background 150ms ease, transform 150ms ease;
}

.ke-question-item:hover,
.ke-question-item.is-active {
  background: color-mix(in srgb, var(--ka-surface-elevated) 88%, transparent);
}

.ke-question-item:active {
  transform: scale(0.99);
}

.ke-state-dot {
  width: 8px;
  height: 8px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--ka-red);
}

.ke-question-item.is-pass .ke-state-dot {
  background: var(--ka-green);
}

.ke-question-main {
  display: grid;
  min-width: 0;
  gap: 3px;
}

.ke-question-main strong,
.ke-question-main small,
.ke-question-main em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ke-question-main strong {
  font-size: 13px;
  line-height: 1.35;
}

.ke-question-main small,
.ke-question-main em,
.ke-question-meta,
.ke-muted-line {
  color: var(--ka-text-tertiary);
  font-size: 12px;
  font-style: normal;
}

.ke-question-meta {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.ke-question-meta b,
.ke-question-meta i {
  border-radius: 6px;
  background: var(--ka-surface-muted);
  color: var(--ka-text-secondary);
  font-size: 11px;
  font-style: normal;
  padding: 3px 6px;
}

.ke-diagnostic-pane {
  overflow: auto;
  padding: 16px;
}

.ke-diagnostic-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--ka-border);
  padding-bottom: 14px;
}

.ke-diagnostic-head h4 {
  margin: 4px 0;
  color: var(--ka-text-primary);
  font-size: 20px;
  line-height: 1.25;
}

.ke-diagnostic-head p {
  margin: 0;
  color: var(--ka-text-tertiary);
  font-size: 12px;
}

.ke-diagnostic-section {
  display: grid;
  gap: 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--ka-border) 70%, transparent);
  padding: 16px 0;
}

.ke-diagnostic-section h5 {
  margin: 0;
  color: var(--ka-text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.ke-reason-list,
.ke-claim-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.ke-reason-list li {
  border-radius: 8px;
  background: color-mix(in srgb, var(--ka-red) 10%, transparent);
  color: var(--ka-red);
  padding: 9px 10px;
}

.ke-answer-block {
  overflow: auto;
  max-height: 260px;
  margin: 0;
  border-radius: 8px;
  background: color-mix(in srgb, var(--ka-surface-muted) 80%, transparent);
  color: var(--ka-text-primary);
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  padding: 12px;
  white-space: pre-wrap;
}

.ke-rule-grid,
.ke-metric-list {
  display: grid;
  gap: 8px;
}

.ke-rule-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.ke-rule-grid span,
.ke-metric-row {
  border-radius: 8px;
  background: var(--ka-surface-muted);
  color: var(--ka-text-tertiary);
  padding: 8px 10px;
}

.ke-metric-row {
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
}

.ke-metric-row strong,
.ke-source-list strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ke-source-list {
  display: grid;
  gap: 10px;
}

.ke-source-list article {
  display: grid;
  gap: 7px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--ka-surface-muted) 72%, transparent);
  padding: 12px;
}

.ke-source-list article > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ke-source-list p,
.ke-source-list blockquote,
.ke-claim-list small {
  margin: 0;
  color: var(--ka-text-tertiary);
  font-size: 12px;
  line-height: 1.55;
}

.ke-source-list blockquote {
  color: var(--ka-text-secondary);
}

.ke-claim-list li {
  display: grid;
  gap: 4px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--ka-red) 8%, transparent);
  color: var(--ka-text-primary);
  padding: 10px;
}

.is-pass {
  color: var(--ka-green);
}

.is-fail {
  color: var(--ka-red);
}

.is-skip {
  color: var(--ka-text-tertiary);
}

.ke-snapshot {
  padding: 12px 16px;
}

.ke-snapshot pre {
  overflow: auto;
  white-space: pre-wrap;
}

@media (max-width: 900px) {
  .ke-diagnostic-shell {
    height: auto;
    grid-template-columns: 1fr;
    overflow: visible;
  }

  .ke-question-pane {
    max-height: 320px;
    border-right: 0;
    border-bottom: 1px solid var(--ka-border);
  }

  .ke-rule-grid,
  .ke-metric-row {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .ke-question-item {
    transition: none;
  }
}
</style>
