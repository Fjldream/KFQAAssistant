<template>
  <section class="ke-center">
    <header class="ke-header">
      <div><p>KingIAsk Quality</p><h1>评测中心</h1></div>
      <div class="ke-actions">
        <button v-if="!isRunning" class="ke-run" type="button" data-testid="run-evaluation" @click="runEvaluation"><Play :size="16" aria-hidden="true" />运行评测</button>
        <button v-else class="ke-run ke-run--danger" type="button" data-testid="abort-evaluation" @click="abortEvaluation"><Square :size="16" aria-hidden="true" />中止评测</button>
        <button class="ke-run ke-run--secondary" type="button" data-testid="approve-baseline" :disabled="!canApproveBaseline" @click="approvalOpen = true">批准基准</button>
      </div>
    </header>

    <p v-if="isRunning" class="ke-status">后端正在运行评测：{{ selectedDetail?.summary.completed_count ?? 0 }} / {{ selectedDetail?.summary.case_total ?? 0 }}。</p>
    <p v-if="errorMessage" class="ke-error">{{ errorMessage }}</p>

    <EvaluationOverview :detail="selectedDetail" />
    <EvaluationComparePanel :comparison="comparison" :baseline="selectedBaseline" />

    <div class="ke-layout">
      <div class="ke-stack">
        <EvaluationCasesTable :cases="cases" />
        <EvaluationRunsTable :runs="runs" :selected-run-id="selectedRunId" @select="selectRun" />
      </div>
      <EvaluationRunDetail :detail="selectedDetail" />
    </div>

    <div v-if="approvalOpen" class="ke-modal" role="dialog" aria-modal="true" aria-label="批准基准">
      <form class="ke-modal__content" @submit.prevent="approveSelectedRun">
        <h2>批准基准</h2>
        <label>批准人<input v-model="approverName" data-testid="approver-name" required maxlength="100" /></label>
        <label>备注<textarea v-model="approvalNote" maxlength="500"></textarea></label>
        <div class="ke-modal__actions"><button type="button" @click="approvalOpen = false">取消</button><button class="ke-run" data-testid="confirm-baseline" type="submit" :disabled="!approverName.trim()">确认批准</button></div>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Play, Square } from "lucide-vue-next";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import EvaluationCasesTable from "./components/EvaluationCasesTable.vue";
import EvaluationComparePanel from "./components/EvaluationComparePanel.vue";
import EvaluationOverview from "./components/EvaluationOverview.vue";
import EvaluationRunDetail from "./components/EvaluationRunDetail.vue";
import EvaluationRunsTable from "./components/EvaluationRunsTable.vue";
import type { EvaluationApiClient } from "./api";
import type { BaselineApproval, ComparisonResult, EvaluationCase, EvaluationRunDetail as Detail, EvaluationRunSummary } from "./types";

const props = defineProps<{ client: EvaluationApiClient }>();
const cases = ref<EvaluationCase[]>([]);
const runs = ref<EvaluationRunSummary[]>([]);
const baselines = ref<BaselineApproval[]>([]);
const selectedRunId = ref<string | null>(null);
const selectedDetail = ref<Detail | null>(null);
const comparison = ref<ComparisonResult | null>(null);
const errorMessage = ref("");
const isRunning = ref(false);
const approvalOpen = ref(false);
const approverName = ref("");
const approvalNote = ref("");
let pollTimer: ReturnType<typeof setTimeout> | null = null;
let disposed = false;
const createdRunMetadata = new Map<string, Pick<EvaluationRunSummary, "suite_id" | "mode">>();

const activeStatuses = new Set(["created", "running", "scoring"]);
const selectedSuiteId = computed(() => selectedDetail.value?.summary.suite_id ?? selectedDetail.value?.snapshot?.suite_id ?? "core");
const selectedBaseline = computed(() => baselines.value.find((item) => item.suite_id === selectedSuiteId.value) ?? null);
const canApproveBaseline = computed(() => {
  const summary = selectedDetail.value?.summary;
  return summary?.status === "completed" && summary.mode === "calibration" && summary.suite_id === selectedSuiteId.value;
});

function stopPolling(): void {
  if (pollTimer !== null) clearTimeout(pollTimer);
  pollTimer = null;
}

async function refreshComparison(runId: string): Promise<void> {
  try { comparison.value = await props.client.compareRun(runId); } catch { comparison.value = null; }
}

async function refreshRuns(): Promise<void> {
  runs.value = await props.client.listEvaluationRuns();
}

async function pollRun(runId: string): Promise<void> {
  stopPolling();
  try {
    const detail = await props.client.getRun(runId);
    if (disposed || selectedRunId.value !== runId) return;
    const summary = { ...createdRunMetadata.get(runId), ...detail.summary };
    selectedDetail.value = { ...detail, summary };
    isRunning.value = activeStatuses.has(summary.status);
    if (isRunning.value) {
      pollTimer = setTimeout(() => void pollRun(runId), 1000);
      return;
    }
    await refreshRuns();
    await refreshComparison(runId);
  } catch (error) {
    if (!disposed) errorMessage.value = error instanceof Error ? error.message : "评测运行加载失败。";
    isRunning.value = false;
  }
}

async function loadEvaluationCenter(): Promise<void> {
  try {
    const [suites, nextRuns, nextBaselines] = await Promise.all([props.client.listSuites(), props.client.listEvaluationRuns(), props.client.listBaselines()]);
    cases.value = suites.find((suite) => suite.id === "core")?.cases ?? suites[0]?.cases ?? [];
    runs.value = nextRuns;
    baselines.value = nextBaselines;
    const latest = nextRuns[0];
    if (latest) await selectRun(latest.run_id);
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : "评测中心加载失败。"; }
}

async function runEvaluation(): Promise<void> {
  try {
    errorMessage.value = "";
    const summary = await props.client.createRun({ suite_id: "core", mode: "calibration" });
    createdRunMetadata.set(summary.run_id, { suite_id: "core", mode: "calibration" });
    selectedRunId.value = summary.run_id;
    isRunning.value = activeStatuses.has(summary.status);
    await pollRun(summary.run_id);
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : "评测运行创建失败。"; isRunning.value = false; }
}

async function abortEvaluation(): Promise<void> {
  if (!selectedRunId.value) return;
  try {
    const summary = await props.client.cancelRun(selectedRunId.value);
    stopPolling();
    isRunning.value = false;
    selectedDetail.value = { ...(selectedDetail.value ?? { gate_result: { outcome: "INVALID", reasons: [] }, case_results: [] }), summary };
    await refreshRuns();
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : "评测取消失败。"; }
}

async function selectRun(runId: string): Promise<void> {
  selectedRunId.value = runId;
  errorMessage.value = "";
  await pollRun(runId);
}

async function approveSelectedRun(): Promise<void> {
  if (!selectedRunId.value || !canApproveBaseline.value) return;
  try {
    await props.client.approveBaseline(selectedRunId.value, { approved_by: approverName.value.trim(), note: approvalNote.value.trim() || undefined });
    approvalOpen.value = false;
    approverName.value = "";
    approvalNote.value = "";
    baselines.value = await props.client.listBaselines();
    await refreshComparison(selectedRunId.value);
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : "基准批准失败。"; }
}

onMounted(() => { void loadEvaluationCenter(); });
onBeforeUnmount(() => { disposed = true; stopPolling(); });
</script>

<style scoped>
.ke-center { display: flex; height: 100%; min-height: 0; flex-direction: column; gap: 16px; padding: 72px 28px 24px; overflow: hidden; }
.ke-header,.ke-overview,.ke-compare,.ke-layout { width: min(1180px, 100%); margin: 0 auto; }
.ke-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }.ke-header p,.ke-header h1 { margin: 0; }.ke-header p { color: var(--ka-text-tertiary); font-size: 12px; font-weight: 700; letter-spacing: 0; text-transform: uppercase; }.ke-header h1 { font-size: 28px; line-height: 1.15; }.ke-actions { display:flex; gap:8px; }
.ke-run { display:inline-flex; height:38px; align-items:center; gap:8px; border-radius:8px; background:var(--ka-accent); color:var(--ka-on-accent); font-weight:700; padding:0 14px; }.ke-run:disabled { cursor:not-allowed; opacity:.45; }.ke-run--danger { background:var(--ka-red); }.ke-run--secondary { background:var(--ka-surface-muted); color:var(--ka-text-secondary); }
.ke-error,.ke-status { width:min(1180px, 100%); margin:0 auto; border-radius:8px; padding:10px 12px; }.ke-error { background:var(--ka-red-soft); color:var(--ka-red); }.ke-status { background:var(--ka-accent-soft); color:var(--ka-accent-strong); }
.ke-layout { display:grid; min-height:0; flex:1; grid-template-columns:420px minmax(0,1fr); gap:14px; }.ke-stack { display:grid; min-height:0; grid-template-rows:minmax(0,1fr) minmax(0,.8fr); gap:14px; }
:deep(.ke-overview) { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; }:deep(.ke-compare) { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }:deep(.ke-metric),:deep(.ke-gate),:deep(.ke-compare > div),:deep(.ke-panel),:deep(.ke-detail) { border:1px solid var(--ka-border); border-radius:8px; background:var(--ka-surface-elevated); box-shadow:var(--ka-shadow-soft); }:deep(.ke-metric),:deep(.ke-gate),:deep(.ke-compare > div) { display:flex; min-height:78px; flex-direction:column; justify-content:center; gap:4px; padding:12px; }:deep(.ke-metric span),:deep(.ke-gate span),:deep(.ke-compare span) { color:var(--ka-text-tertiary); font-size:12px; }:deep(.ke-metric strong),:deep(.ke-gate strong),:deep(.ke-compare strong) { font-size:22px; }:deep(.is-pass) { color:var(--ka-green); }:deep(.is-fail),:deep(.is-invalid) { color:var(--ka-red); }
:deep(.ke-panel),:deep(.ke-detail) { min-height:0; overflow:hidden; }:deep(.ke-panel__head) { display:flex; height:46px; align-items:center; justify-content:space-between; border-bottom:1px solid var(--ka-border); padding:0 14px; }:deep(.ke-panel__head h3) { margin:0; font-size:14px; }:deep(.ke-panel__head span),:deep(.ke-row__main small),:deep(.ke-type),:deep(.ke-empty),:deep(.ke-result small),:deep(.ke-turn small) { color:var(--ka-text-tertiary); font-size:12px; }:deep(.ke-table),:deep(.ke-result-list) { height:calc(100% - 46px); overflow:auto; padding:8px; }:deep(.ke-row) { display:grid; width:100%; grid-template-columns:minmax(0,1fr) auto auto; align-items:center; gap:10px; border-radius:7px; padding:10px; text-align:left; }:deep(.ke-row:hover),:deep(.ke-row.is-active) { background:var(--ka-surface-muted); }:deep(.ke-row__main) { display:grid; min-width:0; gap:2px; }:deep(.ke-row__main strong),:deep(.ke-row__main small) { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }:deep(.ke-badge) { border-radius:6px; background:var(--ka-surface-muted); color:var(--ka-text-secondary); font-size:12px; font-weight:700; padding:3px 7px; }
.ke-modal { position:fixed; z-index:10; inset:0; display:grid; place-items:center; background:rgb(0 0 0 / 35%); }.ke-modal__content { display:grid; width:min(420px,calc(100% - 32px)); gap:14px; border-radius:8px; background:var(--ka-surface-elevated); padding:20px; }.ke-modal__content h2 { margin:0; font-size:18px; }.ke-modal label { display:grid; gap:6px; color:var(--ka-text-secondary); font-size:13px; }.ke-modal input,.ke-modal textarea { width:100%; border:1px solid var(--ka-border); border-radius:6px; background:var(--ka-surface); color:inherit; padding:8px; }.ke-modal__actions { display:flex; justify-content:flex-end; gap:8px; }
@media (max-width:980px) { :deep(.ke-overview) { grid-template-columns:repeat(2,minmax(0,1fr)); }.ke-layout { grid-template-columns:1fr; }.ke-header { align-items:flex-start; flex-direction:column; } }
</style>
