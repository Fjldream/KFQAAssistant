from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationRunMode(str, Enum):
    CALIBRATION = "calibration"
    BLOCKING = "blocking"


class EvaluationRunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    SCORING = "scoring"
    COMPLETED = "completed"
    INVALID = "INVALID"
    CANCELLED = "cancelled"


class CreateEvaluationRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suite_id: str = Field(min_length=1)
    mode: EvaluationRunMode


class ApproveBaselineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_by: str = Field(min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("approved_by")
    @classmethod
    def normalize_approved_by(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("approved_by must not be blank")
        return value


class EvaluationRunSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    status: EvaluationRunStatus
    case_total: int
    case_passed: int
    pass_rate: float
    p0_total: int
    p0_passed: int
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    single_total: int = 0
    single_passed: int = 0
    dialogue_total: int = 0
    dialogue_passed: int = 0
    category_pass_rates: dict[str, float] = Field(default_factory=dict)
    avg_faithfulness_score: float | None = None
    knowledge_base_id: str | None = None
    completed_count: int = 0
    error_count: int = 0
    judge_coverage: float = 0.0
    missing_judge_metrics: list[str] = Field(default_factory=list)
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
    mode: EvaluationRunMode | None = None


class BaselineApprovalResponse(BaseModel):
    suite_id: str
    run_id: str
    approved_by: str | None = None
    note: str | None = None
    approved_at: str | None = None


class RunEvaluationCaseRequest(BaseModel):
    include_dialogues: bool = True


class TurnResultPayload(BaseModel):
    question: str
    answer: str
    standalone_question: str | None = None
    passed: bool
    keyword_passed: bool
    source_passed: bool
    image_passed: bool
    no_answer_passed: bool
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    matched_source_keywords: list[str] = Field(default_factory=list)
    missing_source_keywords: list[str] = Field(default_factory=list)
    forbidden_source_matches: list[str] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    image_count: int = 0
    source_count: int = 0
    elapsed_ms: float = 0.0
    faithfulness_score: float | None = None
    faithfulness_claims: list[dict] = Field(default_factory=list)
    faithfulness_elapsed_ms: float = 0.0


class CaseResultPayload(BaseModel):
    case_id: str
    category: str
    priority: str
    case_type: str
    passed: bool
    turn_results: list[TurnResultPayload]
    failure_reasons: list[str] = Field(default_factory=list)
    elapsed_ms: float = 0.0


class SaveProgressiveRunRequest(BaseModel):
    case_results: list[CaseResultPayload]
    config: dict = Field(default_factory=dict)
