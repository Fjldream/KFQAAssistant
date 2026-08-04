from pydantic import BaseModel, Field


class CreateEvaluationRunRequest(BaseModel):
    include_dialogues: bool = True
    include_load_test: bool = False


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
