import hashlib
import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


NonEmptyIdentifier = Annotated[str, Field(min_length=1)]


class RequiredFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    required: bool = True


class EvaluationThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_correctness: float = Field(ge=0, le=1)
    faithfulness: float = Field(ge=0, le=1)
    p1_required_fact_coverage: float = Field(ge=0, le=1)


class EvaluationTurnSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    reference_answer: str = ""
    required_facts: list[RequiredFact] = Field(default_factory=list)
    keyword_anchors: list[str] = Field(default_factory=list)
    forbidden_facts: list[str] = Field(default_factory=list)
    expected_source_ids: list[NonEmptyIdentifier] = Field(default_factory=list)
    expected_chunk_ids: list[NonEmptyIdentifier] = Field(default_factory=list)
    forbidden_source_ids: list[NonEmptyIdentifier] = Field(default_factory=list)
    expect_no_answer: bool = False
    expect_images: bool = False
    min_sources: int = Field(default=0, ge=0)
    min_images: int = Field(default=0, ge=0)


class EvaluationCaseSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    priority: Literal["P0", "P1"] = "P1"
    tags: list[str] = Field(default_factory=list)
    turns: list[EvaluationTurnSpec] = Field(min_length=1)
    legacy_unreviewed: bool = False

    @model_validator(mode="before")
    @classmethod
    def normalize_single_turn(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        data = dict(value)
        turn_fields = set(EvaluationTurnSpec.model_fields)
        top_level_turn = {key: data.pop(key) for key in turn_fields if key in data}
        if "turns" in data:
            if top_level_turn:
                raise ValueError("用例不能同时声明单轮字段和 turns")
            return data

        data["turns"] = [top_level_turn]
        return data

    @model_validator(mode="after")
    def require_facts_for_answerable_p0_turns(self) -> "EvaluationCaseSpec":
        if self.priority == "P0":
            for turn in self.turns:
                if not turn.expect_no_answer and not any(fact.required for fact in turn.required_facts):
                    raise ValueError("P0 可回答用例必须包含至少一个必需事实")
        return self


class EvaluationSuite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    default_thresholds: EvaluationThresholds
    cases: list[EvaluationCaseSpec]

    @model_validator(mode="after")
    def require_unique_case_ids(self) -> "EvaluationSuite":
        if not self.cases:
            raise ValueError("评测套件至少包含一个用例")
        ids = [case.id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("用例 ID 重复")
        return self


def suite_content_hash(suite: EvaluationSuite) -> str:
    canonical_json = json.dumps(
        suite.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
