from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class RunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    SCORING = "scoring"
    COMPLETED = "completed"
    INVALID = "INVALID"
    CANCELLED = "cancelled"


class GateMode(str, Enum):
    CALIBRATION = "CALIBRATION"
    BLOCKING = "BLOCKING"


class GateOutcome(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    INVALID = "INVALID"


ALLOWED_RUN_TRANSITIONS: Mapping[RunStatus, frozenset[RunStatus]] = MappingProxyType({
    RunStatus.CREATED: frozenset({RunStatus.RUNNING}),
    RunStatus.RUNNING: frozenset({RunStatus.SCORING, RunStatus.INVALID, RunStatus.CANCELLED}),
    RunStatus.SCORING: frozenset({RunStatus.COMPLETED, RunStatus.INVALID}),
    RunStatus.COMPLETED: frozenset(),
    RunStatus.INVALID: frozenset(),
    RunStatus.CANCELLED: frozenset(),
})


def can_transition(source: RunStatus, target: RunStatus) -> bool:
    return target in ALLOWED_RUN_TRANSITIONS[source]


class MetricStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float | None
    status: MetricStatus
    threshold: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0
    token_usage: Any | None = None
    error_code: str | None = None


# 表示一个用户问题对应的单轮评测规则，是单轮和连续对话评测的最小单元。
@dataclass(frozen=True)
class EvaluationTurn:
    question: str
    expected_keywords: list[str] = field(default_factory=list)
    expected_keyword_groups: list[list[str]] = field(default_factory=list)
    expected_source_keywords: list[str] = field(default_factory=list)
    expected_source_keyword_groups: list[list[str]] = field(default_factory=list)
    forbidden_source_keywords: list[str] = field(default_factory=list)
    expect_images: bool = False
    expect_no_answer: bool = False
    min_sources: int = 0
    min_images: int = 0
    reference_answer: str = ""
    required_facts: list[dict] = field(default_factory=list)
    keyword_anchors: list[str] = field(default_factory=list)
    forbidden_facts: list[str] = field(default_factory=list)
    expected_source_ids: list[str] = field(default_factory=list)
    expected_chunk_ids: list[str] = field(default_factory=list)
    forbidden_source_ids: list[str] = field(default_factory=list)


# 表示一个完整评测用例，单轮用例包含一轮，连续对话用例包含多轮。
@dataclass(frozen=True)
class EvaluationCase:
    id: str
    category: str
    turns: list[EvaluationTurn]
    priority: str = "P1"
    tags: list[str] = field(default_factory=list)
    knowledge_base_id: str | None = None

    @property
    # 根据轮次数判断用例类型，避免在 JSON 中重复维护容易出错的类型字段。
    def case_type(self) -> str:
        return "dialogue" if len(self.turns) > 1 else "single"


# 表示一次用户问题的评测结果，后续会用于报告详情和失败原因展示。
@dataclass(frozen=True)
class TurnResult:
    question: str
    answer: str
    standalone_question: str | None
    passed: bool
    keyword_passed: bool
    source_passed: bool
    image_passed: bool
    no_answer_passed: bool
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    matched_source_keywords: list[str] = field(default_factory=list)
    missing_source_keywords: list[str] = field(default_factory=list)
    forbidden_source_matches: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    image_count: int = 0
    source_count: int = 0
    elapsed_ms: float = 0.0
    faithfulness_score: float | None = None
    faithfulness_claims: list[dict] = field(default_factory=list)
    faithfulness_elapsed_ms: float = 0.0
    metric_results: list[MetricResult] = field(default_factory=list)


# 表示一个评测用例的整体结果，连续对话时会包含多轮 TurnResult。
@dataclass(frozen=True)
class CaseResult:
    case_id: str
    category: str
    priority: str
    case_type: str
    passed: bool
    turn_results: list[TurnResult]
    failure_reasons: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    metric_results: list[MetricResult] = field(default_factory=list)


# 表示一次评测运行的汇总指标，供列表、总览和门禁判断复用。
@dataclass(frozen=True)
class EvaluationRunSummary:
    run_id: str
    status: str | RunStatus
    case_total: int
    case_passed: int
    pass_rate: float
    p0_total: int = 0
    p0_passed: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    single_total: int = 0
    single_passed: int = 0
    dialogue_total: int = 0
    dialogue_passed: int = 0
    category_pass_rates: dict[str, float] = field(default_factory=dict)
    avg_faithfulness_score: float | None = None
    knowledge_base_id: str | None = None
    completed_count: int = 0
    error_count: int = 0
    judge_coverage: float = 0.0
    missing_judge_metrics: list[str] = field(default_factory=list)
    avg_correctness_score: float | None = None
    avg_fact_coverage_score: float | None = None
    avg_retrieval_recall: float | None = None
    avg_retrieval_mrr: float | None = None
    single_p95_latency_ms: float = 0.0
    dialogue_p95_latency_ms: float = 0.0
    total_token_count: int = 0
    estimated_cost: float = 0.0
    suite_id: str | None = None
    suite_version: str | None = None
    suite_hash: str | None = None
    mode: str | None = None

    @property
    def completed_case_count(self) -> int:
        return self.completed_count


# 表示一次评测运行是否满足上线质量门禁，以及不通过的具体原因。
@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GateDecision:
    outcome: GateOutcome
    absolute_reasons: list[str] = field(default_factory=list)
    regression_reasons: list[str] = field(default_factory=list)
    validity_reasons: list[str] = field(default_factory=list)


# 表示两次评测运行之间的用例状态变化。
@dataclass(frozen=True)
class ComparisonResult:
    regressed_case_ids: list[str] = field(default_factory=list)
    recovered_case_ids: list[str] = field(default_factory=list)
    unchanged_failed_case_ids: list[str] = field(default_factory=list)
    new_case_ids: list[str] = field(default_factory=list)
    removed_case_ids: list[str] = field(default_factory=list)
    pass_rate_delta: float = 0.0
    metric_deltas: dict[str, float] = field(default_factory=dict)
    case_regression_reasons: list[str] = field(default_factory=list)


# 表示一次评测运行的完整报告，包含汇总、门禁和所有用例明细。
@dataclass(frozen=True)
class EvaluationRunDetail:
    summary: EvaluationRunSummary
    gate_result: GateResult
    case_results: list[CaseResult] = field(default_factory=list)
    snapshot: dict[str, Any] | None = None


# 表示评测中心首页需要展示的最近运行、上一轮和对比信息。
@dataclass(frozen=True)
class EvaluationOverview:
    latest: EvaluationRunDetail | None
    previous_run_id: str | None
    comparison: ComparisonResult | None
