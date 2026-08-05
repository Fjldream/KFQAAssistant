import { requestJson } from "../../api/client";
import type { ApiSettings } from "../../api/types";
import type {
  ApproveBaselineRequest,
  BaselineApproval,
  ComparisonResult,
  CreateRunRequest,
  EvaluationCase,
  EvaluationRunDetail,
  EvaluationRunSummary,
  EvaluationSuite,
} from "./types";

export interface EvaluationApiClient {
  listSuites: () => Promise<EvaluationSuite[]>;
  listEvaluationRuns: (limit?: number) => Promise<EvaluationRunSummary[]>;
  createRun: (request: CreateRunRequest) => Promise<EvaluationRunSummary>;
  getRun: (runId: string) => Promise<EvaluationRunDetail>;
  cancelRun: (runId: string) => Promise<EvaluationRunSummary>;
  listBaselines: () => Promise<BaselineApproval[]>;
  approveBaseline: (runId: string, request: ApproveBaselineRequest) => Promise<BaselineApproval>;
  compareRun: (runId: string, baselineRunId?: string) => Promise<ComparisonResult>;
}

export function createEvaluationApiClient(settings: ApiSettings): EvaluationApiClient {
  return {
    // The existing read-only case endpoint is the trusted source for the current core Suite.
    listSuites: async () => {
      const cases = await requestJson<EvaluationCase[]>(settings, "/api/evaluation/cases");
      return [{ id: "core", cases }];
    },
    listEvaluationRuns: (limit = 20) =>
      requestJson<EvaluationRunSummary[]>(settings, `/api/evaluation/runs?limit=${limit}`),
    createRun: (request) =>
      requestJson<EvaluationRunSummary>(settings, "/api/evaluation/runs", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    getRun: (runId) => requestJson<EvaluationRunDetail>(settings, `/api/evaluation/runs/${encodeURIComponent(runId)}`),
    cancelRun: (runId) =>
      requestJson<EvaluationRunSummary>(settings, `/api/evaluation/runs/${encodeURIComponent(runId)}/cancel`, { method: "POST" }),
    listBaselines: () => requestJson<BaselineApproval[]>(settings, "/api/evaluation/baselines"),
    approveBaseline: (runId, request) =>
      requestJson<BaselineApproval>(settings, `/api/evaluation/runs/${encodeURIComponent(runId)}/approve-baseline`, {
        method: "POST",
        body: JSON.stringify(request),
      }),
    compareRun: (runId, baselineRunId) => {
      const query = baselineRunId ? `?baseline_run_id=${encodeURIComponent(baselineRunId)}` : "";
      return requestJson<ComparisonResult>(settings, `/api/evaluation/runs/${encodeURIComponent(runId)}/compare${query}`);
    },
  };
}
