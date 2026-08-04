<template>
  <section class="ke-center">
    <header class="ke-header">
      <div>
        <p>KingIAsk Quality</p>
        <h1>评测中心</h1>
      </div>
      <button
        v-if="!isRunning"
        class="ke-run"
        type="button"
        data-testid="run-evaluation"
        @click="runEvaluation"
      >
        <Play :size="16" aria-hidden="true" />
        运行评测
      </button>
      <button
        v-else
        class="ke-run ke-run--danger"
        type="button"
        data-testid="abort-evaluation"
        @click="abortEvaluation"
      >
        <Square :size="16" aria-hidden="true" />
        中止评测
      </button>
    </header>

    <p v-if="isRunning" class="ke-status">
      正在运行评测：{{ completedCount }} / {{ cases.length }}，当前用例会实时更新状态。
    </p>
    <p v-if="errorMessage" class="ke-error">{{ errorMessage }}</p>

    <EvaluationOverview :detail="selectedDetail" />
    <EvaluationComparePanel :comparison="overview?.comparison ?? null" />

    <section class="ke-progress" aria-label="评测进度">
      <div class="ke-progress__bar">
        <span :style="{ width: progressPercent }"></span>
      </div>
      <div class="ke-progress__cases">
        <article
          v-for="item in cases"
          :key="item.id"
          class="ke-progress-case"
          :class="`is-${caseStatuses[item.id]?.state ?? 'pending'}`"
        >
          <span>{{ caseStatusLabel(caseStatuses[item.id]?.state ?? "pending") }}</span>
          <strong>{{ item.id }}</strong>
          <small>{{ caseStatuses[item.id]?.message || item.turns[0]?.question }}</small>
        </article>
      </div>
    </section>

    <div class="ke-layout">
      <div class="ke-stack">
        <EvaluationCasesTable :cases="cases" />
        <EvaluationRunsTable :runs="runs" :selected-run-id="selectedRunId" @select="selectRun" />
      </div>
      <EvaluationRunDetail :detail="selectedDetail" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { Play, Square } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import EvaluationCasesTable from "./components/EvaluationCasesTable.vue";
import EvaluationComparePanel from "./components/EvaluationComparePanel.vue";
import EvaluationOverview from "./components/EvaluationOverview.vue";
import EvaluationRunDetail from "./components/EvaluationRunDetail.vue";
import EvaluationRunsTable from "./components/EvaluationRunsTable.vue";
import type { EvaluationApiClient } from "./api";
import type {
  CaseResult,
  EvaluationCase,
  EvaluationOverviewResponse,
  EvaluationRunDetail as EvaluationRunDetailModel,
  EvaluationRunSummary,
} from "./types";

type CaseRunState = "pending" | "running" | "passed" | "failed" | "error" | "aborted";

interface CaseRunStatus {
  state: CaseRunState;
  message: string;
}

const props = defineProps<{
  client: EvaluationApiClient;
}>();

const cases = ref<EvaluationCase[]>([]);
const runs = ref<EvaluationRunSummary[]>([]);
const overview = ref<EvaluationOverviewResponse | null>(null);
const selectedRunId = ref<string | null>(null);
const selectedDetail = ref<EvaluationRunDetailModel | null>(null);
const isRunning = ref(false);
const errorMessage = ref("");
const caseStatuses = ref<Record<string, CaseRunStatus>>({});
const abortRequested = ref(false);
const activeAbortController = ref<AbortController | null>(null);

const completedCount = computed(() =>
  Object.values(caseStatuses.value).filter((status) =>
    ["passed", "failed", "error", "aborted"].includes(status.state),
  ).length,
);
const progressPercent = computed(() => {
  if (!cases.value.length) {
    return "0%";
  }
  return `${Math.round((completedCount.value / cases.value.length) * 100)}%`;
});

// 初始化评测中心所需数据，包括用例、历史和最近报告。
async function loadEvaluationCenter(): Promise<void> {
  try {
    errorMessage.value = "";
    const [nextCases, nextOverview, nextRuns] = await Promise.all([
      props.client.listEvaluationCases(),
      props.client.getEvaluationOverview(),
      props.client.listEvaluationRuns(),
    ]);
    cases.value = nextCases;
    overview.value = nextOverview;
    runs.value = nextRuns;
    selectedDetail.value = nextOverview.latest;
    selectedRunId.value = nextOverview.latest?.summary.run_id ?? nextRuns[0]?.run_id ?? null;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "评测中心加载失败。";
  }
}

// 触发渐进式评测运行：逐条调用后端接口，逐条刷新状态和报告区。
async function runEvaluation(): Promise<void> {
  try {
    isRunning.value = true;
    abortRequested.value = false;
    errorMessage.value = "";
    caseStatuses.value = Object.fromEntries(
      cases.value.map((item) => [item.id, { state: "pending", message: "等待运行" }]),
    );
    const completedResults: CaseResult[] = [];
    selectedDetail.value = null;

    for (const item of cases.value) {
      if (abortRequested.value) {
        caseStatuses.value[item.id] = { state: "aborted", message: "已中止" };
        continue;
      }
      caseStatuses.value[item.id] = { state: "running", message: "运行中" };
      activeAbortController.value = new AbortController();
      try {
        const result = await props.client.runEvaluationCase(
          item.id,
          { include_dialogues: true },
          activeAbortController.value.signal,
        );
        completedResults.push(result);
        caseStatuses.value[item.id] = {
          state: result.passed ? "passed" : "failed",
          message: result.passed ? "通过" : result.failure_reasons?.[0] || "未通过",
        };
        selectedDetail.value = buildPreviewDetail(completedResults);
      } catch (error) {
        const isAbort = error instanceof DOMException && error.name === "AbortError";
        caseStatuses.value[item.id] = {
          state: isAbort ? "aborted" : "error",
          message: isAbort ? "已中止" : error instanceof Error ? error.message : "接口错误",
        };
        if (isAbort || abortRequested.value) {
          break;
        }
        errorMessage.value = error instanceof Error ? error.message : "评测运行失败。";
      } finally {
        activeAbortController.value = null;
      }
    }

    if (abortRequested.value) {
      errorMessage.value = "评测已中止，未保存本次运行。";
      return;
    }

    const detail = await props.client.saveProgressiveRun({
      case_results: completedResults,
      config: { include_dialogues: true, include_load_test: false },
    });
    selectedDetail.value = detail;
    selectedRunId.value = detail.summary.run_id;
    overview.value = await props.client.getEvaluationOverview();
    runs.value = await props.client.listEvaluationRuns();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "评测运行失败。";
  } finally {
    isRunning.value = false;
  }
}

// 中止渐进式评测：停止后续用例，并取消当前浏览器请求。
function abortEvaluation(): void {
  abortRequested.value = true;
  activeAbortController.value?.abort();
}

// 根据单条用例状态返回页面展示文案。
function caseStatusLabel(state: CaseRunState): string {
  const labels: Record<CaseRunState, string> = {
    pending: "等待中",
    running: "运行中",
    passed: "通过",
    failed: "失败",
    error: "接口错误",
    aborted: "已中止",
  };
  return labels[state];
}

// 用已完成用例临时构造报告详情，让右侧报告区可以边跑边显示。
function buildPreviewDetail(caseResults: CaseResult[]): EvaluationRunDetailModel {
  const passed = caseResults.filter((result) => result.passed).length;
  return {
    summary: {
      run_id: "运行中",
      status: "running",
      case_total: cases.value.length,
      case_passed: passed,
      pass_rate: caseResults.length ? passed / caseResults.length : 0,
    },
    gate_result: { passed: false, reasons: [] },
    case_results: caseResults,
  };
}

// 选择历史运行并加载对应的详细报告。
async function selectRun(runId: string): Promise<void> {
  try {
    selectedRunId.value = runId;
    selectedDetail.value = await props.client.getEvaluationRun(runId);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "评测报告加载失败。";
  }
}

onMounted(() => {
  void loadEvaluationCenter();
});
</script>

<style scoped>
.ke-center {
  display: flex;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  gap: 16px;
  padding: 72px 28px 24px;
  overflow: hidden;
}

.ke-header,
.ke-overview,
.ke-compare,
.ke-layout {
  width: min(1180px, 100%);
  margin: 0 auto;
}

.ke-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.ke-header p,
.ke-header h1 {
  margin: 0;
}

.ke-header p {
  color: var(--ka-text-tertiary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.ke-header h1 {
  font-size: 28px;
  line-height: 1.15;
}

.ke-run {
  display: inline-flex;
  height: 38px;
  align-items: center;
  gap: 8px;
  border-radius: 8px;
  background: var(--ka-accent);
  color: var(--ka-on-accent);
  font-weight: 700;
  padding: 0 14px;
}

.ke-run--danger {
  background: var(--ka-red);
}

.ke-error,
.ke-status {
  width: min(1180px, 100%);
  margin: 0 auto;
  border-radius: 8px;
  padding: 10px 12px;
}

.ke-error {
  background: var(--ka-red-soft);
  color: var(--ka-red);
}

.ke-status {
  background: var(--ka-accent-soft);
  color: var(--ka-accent-strong);
}

.ke-progress {
  display: grid;
  width: min(1180px, 100%);
  max-height: 132px;
  min-height: 0;
  gap: 8px;
  margin: 0 auto;
  overflow: hidden;
}

.ke-progress__bar {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--ka-surface-muted);
}

.ke-progress__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--ka-accent);
  transition: width 220ms var(--ka-ease-out);
}

.ke-progress__cases {
  display: grid;
  max-height: 118px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 8px;
  overflow: auto;
}

.ke-progress-case {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 2px 8px;
  border: 1px solid var(--ka-border);
  border-radius: 8px;
  background: var(--ka-surface-elevated);
  padding: 8px 10px;
}

.ke-progress-case span {
  grid-row: span 2;
  align-self: center;
  border-radius: 6px;
  background: var(--ka-surface-muted);
  color: var(--ka-text-secondary);
  font-size: 12px;
  font-weight: 700;
  padding: 3px 7px;
}

.ke-progress-case strong,
.ke-progress-case small {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ke-progress-case strong {
  font-size: 13px;
}

.ke-progress-case small {
  color: var(--ka-text-tertiary);
  font-size: 12px;
}

.ke-progress-case.is-running span {
  background: var(--ka-accent-soft);
  color: var(--ka-accent-strong);
}

.ke-progress-case.is-passed span {
  background: var(--ka-green-soft);
  color: var(--ka-green);
}

.ke-progress-case.is-failed span,
.ke-progress-case.is-error span,
.ke-progress-case.is-aborted span {
  background: var(--ka-red-soft);
  color: var(--ka-red);
}

.ke-overview,
.ke-compare {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.ke-compare {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

:deep(.ke-metric),
:deep(.ke-gate),
.ke-compare > div,
:deep(.ke-panel),
:deep(.ke-detail) {
  border: 1px solid var(--ka-border);
  border-radius: 8px;
  background: var(--ka-surface-elevated);
  box-shadow: var(--ka-shadow-soft);
}

:deep(.ke-metric),
:deep(.ke-gate),
.ke-compare > div {
  display: flex;
  min-height: 78px;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  padding: 12px;
}

:deep(.ke-metric span),
:deep(.ke-gate span),
.ke-compare span {
  color: var(--ka-text-tertiary);
  font-size: 12px;
}

:deep(.ke-metric strong),
:deep(.ke-gate strong),
.ke-compare strong {
  font-size: 22px;
}

:deep(.is-pass) {
  color: var(--ka-green);
}

:deep(.is-fail) {
  color: var(--ka-red);
}

.ke-layout {
  display: grid;
  min-height: 0;
  flex: 1;
  grid-template-columns: 420px minmax(0, 1fr);
  gap: 14px;
}

.ke-stack {
  display: grid;
  min-height: 0;
  grid-template-rows: minmax(0, 1fr) minmax(0, 0.8fr);
  gap: 14px;
}

:deep(.ke-panel),
:deep(.ke-detail) {
  min-height: 0;
  overflow: hidden;
}

:deep(.ke-panel__head) {
  display: flex;
  height: 46px;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--ka-border);
  padding: 0 14px;
}

:deep(.ke-panel__head h3) {
  margin: 0;
  font-size: 14px;
}

:deep(.ke-panel__head span) {
  color: var(--ka-text-tertiary);
  font-size: 12px;
}

:deep(.ke-table),
:deep(.ke-result-list) {
  height: calc(100% - 46px);
  overflow: auto;
  padding: 8px;
}

:deep(.ke-row) {
  display: grid;
  width: 100%;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 10px;
  border-radius: 7px;
  padding: 10px;
  text-align: left;
}

:deep(.ke-row:hover),
:deep(.ke-row.is-active) {
  background: var(--ka-surface-muted);
}

:deep(.ke-row__main) {
  display: grid;
  min-width: 0;
  gap: 2px;
}

:deep(.ke-row__main strong),
:deep(.ke-row__main small) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.ke-row__main small),
:deep(.ke-type),
:deep(.ke-empty) {
  color: var(--ka-text-tertiary);
  font-size: 12px;
}

:deep(.ke-badge) {
  border-radius: 6px;
  background: var(--ka-surface-muted);
  color: var(--ka-text-secondary);
  font-size: 12px;
  font-weight: 700;
  padding: 3px 7px;
}

:deep(.ke-result) {
  border-bottom: 1px solid var(--ka-border);
  padding: 12px 6px;
}

:deep(.ke-result header) {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

:deep(.ke-result small),
:deep(.ke-turn small) {
  display: block;
  color: var(--ka-text-tertiary);
}

:deep(.ke-reason) {
  color: var(--ka-red);
}

:deep(details) {
  margin-top: 10px;
}

:deep(summary) {
  cursor: pointer;
  font-weight: 650;
}

:deep(.ke-turn) {
  margin-top: 8px;
  border-radius: 8px;
  background: var(--ka-surface-muted);
  padding: 10px;
}

@media (max-width: 980px) {
  .ke-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ke-layout {
    grid-template-columns: 1fr;
  }
}
</style>
