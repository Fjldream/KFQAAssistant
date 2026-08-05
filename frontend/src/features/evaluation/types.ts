export type RunStatus = "created" | "running" | "scoring" | "completed" | "INVALID" | "cancelled";
export type GateMode = "calibration" | "blocking";
export type GateOutcome = "PASSED" | "FAILED" | "INVALID";
export type MetricStatus = "PASSED" | "FAILED" | "ERROR" | "SKIPPED";

export interface EvaluationTurn {
  question: string;
  expected_keywords?: string[];
  expected_keyword_groups?: string[][];
  expected_source_keywords?: string[];
  expected_source_keyword_groups?: string[][];
  forbidden_source_keywords?: string[];
  expect_images?: boolean;
  expect_no_answer?: boolean;
  min_sources?: number;
  min_images?: number;
}

export interface EvaluationCase {
  id: string;
  category: string;
  priority: string;
  tags: string[];
  case_type: "single" | "dialogue";
  turns: EvaluationTurn[];
}

export interface EvaluationSuite {
  id: string;
  version?: string;
  cases: EvaluationCase[];
}

export interface MetricResult {
  name: string;
  score: number | null;
  status: MetricStatus;
  threshold?: number | null;
  details?: Record<string, unknown>;
  elapsed_ms?: number;
  error_code?: string | null;
}

export interface EvaluationRunSummary {
  run_id: string;
  status: RunStatus;
  case_total: number;
  case_passed: number;
  pass_rate: number;
  p0_total?: number;
  p0_passed?: number;
  avg_latency_ms?: number;
  p95_latency_ms?: number;
  avg_faithfulness_score?: number | null;
  completed_count?: number;
  error_count?: number;
  total_token_count?: number;
  estimated_cost?: number;
  suite_id?: string;
  suite_version?: string;
  suite_hash?: string;
  mode?: GateMode;
}

export interface GateResult {
  passed: boolean;
  reasons: string[];
}

export interface FaithfulnessClaim {
  claim: string;
  supported: boolean;
  evidence: string;
}

export interface TurnResult {
  question: string;
  answer: string;
  standalone_question?: string | null;
  passed: boolean;
  faithfulness_score: number | null;
  faithfulness_claims: FaithfulnessClaim[];
  metric_results: MetricResult[];
}

export interface CaseResult {
  case_id: string;
  category: string;
  priority: string;
  case_type: string;
  passed: boolean;
  turn_results: TurnResult[];
  failure_reasons: string[];
  metric_results: MetricResult[];
}

export interface RunSnapshot {
  suite_id?: string;
  suite_version?: string;
  knowledge_base_id?: string;
  [key: string]: unknown;
}

export interface EvaluationRunDetail {
  summary: EvaluationRunSummary;
  gate_result: GateResult;
  case_results: CaseResult[];
  snapshot?: RunSnapshot | null;
}

export interface BaselineApproval {
  suite_id: string;
  run_id: string;
  approved_by: string | null;
  note: string | null;
  approved_at: string | null;
}

export interface ComparisonResult {
  baseline_run_id?: string | null;
  regressed_case_ids?: string[];
  recovered_case_ids?: string[];
  unchanged_failed_case_ids?: string[];
  new_case_ids?: string[];
  removed_case_ids?: string[];
  pass_rate_delta?: number;
  metric_deltas?: Record<string, number>;
  case_regression_reasons?: string[];
}

export interface CreateRunRequest {
  suite_id: string;
  mode: GateMode;
}

export interface ApproveBaselineRequest {
  approved_by: string;
  note?: string;
}
