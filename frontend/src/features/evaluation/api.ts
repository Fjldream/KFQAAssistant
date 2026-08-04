import { requestJson } from "../../api/client";
import type { ApiSettings } from "../../api/types";
import type {
  ComparisonResult,
  CreateEvaluationRunRequest,
  RunEvaluationCaseRequest,
  SaveProgressiveRunRequest,
  CaseResult,
  EvaluationCase,
  EvaluationOverviewResponse,
  EvaluationRunDetail,
  EvaluationRunSummary,
} from "./types";

export interface EvaluationApiClient {
  listEvaluationCases: () => Promise<EvaluationCase[]>;
  getEvaluationOverview: () => Promise<EvaluationOverviewResponse>;
  listEvaluationRuns: (limit?: number) => Promise<EvaluationRunSummary[]>;
  createEvaluationRun: (request: CreateEvaluationRunRequest) => Promise<EvaluationRunDetail>;
  runEvaluationCase: (
    caseId: string,
    request: RunEvaluationCaseRequest,
    signal?: AbortSignal,
  ) => Promise<CaseResult>;
  saveProgressiveRun: (request: SaveProgressiveRunRequest) => Promise<EvaluationRunDetail>;
  getEvaluationRun: (runId: string) => Promise<EvaluationRunDetail>;
  compareEvaluationRun: (runId: string, baselineRunId?: string) => Promise<ComparisonResult>;
}

// 创建评测中心 API 客户端，复用全局请求封装以保持鉴权和错误处理一致。
export function createEvaluationApiClient(settings: ApiSettings): EvaluationApiClient {
  return {
    listEvaluationCases: () => requestJson<EvaluationCase[]>(settings, "/api/evaluation/cases"),
    getEvaluationOverview: () => requestJson<EvaluationOverviewResponse>(settings, "/api/evaluation/overview"),
    listEvaluationRuns: (limit = 20) =>
      requestJson<EvaluationRunSummary[]>(settings, `/api/evaluation/runs?limit=${limit}`),
    createEvaluationRun: (request: CreateEvaluationRunRequest) =>
      requestJson<EvaluationRunDetail>(settings, "/api/evaluation/runs", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    runEvaluationCase: (caseId: string, request: RunEvaluationCaseRequest, signal?: AbortSignal) =>
      requestJson<CaseResult>(settings, `/api/evaluation/cases/${encodeURIComponent(caseId)}/run`, {
        method: "POST",
        body: JSON.stringify(request),
        signal,
      }),
    saveProgressiveRun: (request: SaveProgressiveRunRequest) =>
      requestJson<EvaluationRunDetail>(settings, "/api/evaluation/runs/progressive", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    getEvaluationRun: (runId: string) =>
      requestJson<EvaluationRunDetail>(settings, `/api/evaluation/runs/${encodeURIComponent(runId)}`),
    compareEvaluationRun: (runId: string, baselineRunId?: string) => {
      const query = baselineRunId ? `?baseline_run_id=${encodeURIComponent(baselineRunId)}` : "";
      return requestJson<ComparisonResult>(settings, `/api/evaluation/runs/${encodeURIComponent(runId)}/compare${query}`);
    },
  };
}
