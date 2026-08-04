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

export interface EvaluationRunSummary {
  run_id: string;
  status: string;
  case_total: number;
  case_passed: number;
  pass_rate: number;
  p0_total?: number;
  p0_passed?: number;
  avg_latency_ms?: number;
  p95_latency_ms?: number;
}

export interface GateResult {
  passed: boolean;
  reasons: string[];
}

export interface TurnResult {
  question: string;
  answer: string;
  standalone_question?: string | null;
  passed: boolean;
  missing_keywords?: string[];
  missing_source_keywords?: string[];
  forbidden_source_matches?: string[];
  image_count?: number;
  source_count?: number;
  elapsed_ms?: number;
}

export interface CaseResult {
  case_id: string;
  category: string;
  priority: string;
  case_type: string;
  passed: boolean;
  turn_results: TurnResult[];
  failure_reasons?: string[];
  elapsed_ms?: number;
}

export interface EvaluationRunDetail {
  summary: EvaluationRunSummary;
  gate_result: GateResult;
  case_results: CaseResult[];
}

export interface ComparisonResult {
  regressed_case_ids?: string[];
  recovered_case_ids?: string[];
  unchanged_failed_case_ids?: string[];
  new_case_ids?: string[];
  removed_case_ids?: string[];
  pass_rate_delta?: number;
}

export interface EvaluationOverviewResponse {
  latest: EvaluationRunDetail | null;
  previous_run_id: string | null;
  comparison: ComparisonResult | null;
}

export interface CreateEvaluationRunRequest {
  include_dialogues: boolean;
  include_load_test: boolean;
}

export interface RunEvaluationCaseRequest {
  include_dialogues: boolean;
}

export interface SaveProgressiveRunRequest {
  case_results: CaseResult[];
  config: Record<string, unknown>;
}
