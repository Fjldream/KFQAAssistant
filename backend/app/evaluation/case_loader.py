import json
from pathlib import Path
from typing import Any

from app.evaluation.models import EvaluationCase, EvaluationTurn
from app.evaluation.suite import (
    EvaluationCaseSpec,
    EvaluationSuite,
    EvaluationThresholds,
    EvaluationTurnSpec,
    RequiredFact,
)


# 把 JSON 中的一轮配置转换成 EvaluationTurn，缺失规则字段时使用安全默认值。
def _parse_turn(raw_turn: dict[str, Any]) -> EvaluationTurn:
    return EvaluationTurn(
        question=str(raw_turn["question"]),
        expected_keywords=list(raw_turn.get("expected_keywords", [])),
        expected_keyword_groups=[list(group) for group in raw_turn.get("expected_keyword_groups", [])],
        expected_source_keywords=list(raw_turn.get("expected_source_keywords", [])),
        expected_source_keyword_groups=[
            list(group) for group in raw_turn.get("expected_source_keyword_groups", [])
        ],
        forbidden_source_keywords=list(raw_turn.get("forbidden_source_keywords", [])),
        expect_images=bool(raw_turn.get("expect_images", False)),
        expect_no_answer=bool(raw_turn.get("expect_no_answer", False)),
        min_sources=int(raw_turn.get("min_sources", 0)),
        min_images=int(raw_turn.get("min_images", 0)),
    )


# 把旧版单轮格式或新版多轮格式统一转换成 EvaluationCase。
def _parse_case(raw_case: dict[str, Any], index: int) -> EvaluationCase:
    if "turns" in raw_case:
        turns = [_parse_turn(turn) for turn in raw_case.get("turns", [])]
    else:
        turns = [_parse_turn(raw_case)]

    return EvaluationCase(
        id=str(raw_case.get("id") or f"case-{index}"),
        category=str(raw_case.get("category") or "未分类"),
        priority=str(raw_case.get("priority") or "P1"),
        tags=list(raw_case.get("tags", [])),
        turns=turns,
    )


# 从评测 JSON 文件加载用例列表，文件不存在时返回空列表，方便平台首次启动。
def load_evaluation_cases(path: Path) -> list[EvaluationCase]:
    if not path.exists():
        return []

    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw_cases, dict):
        return [_legacy_case_from_spec(case) for case in load_evaluation_suite(path).cases]
    return [_parse_case(raw_case, index) for index, raw_case in enumerate(raw_cases, start=1)]


def _legacy_case_from_spec(case: EvaluationCaseSpec) -> EvaluationCase:
    return EvaluationCase(
        id=case.id,
        category=case.category,
        priority=case.priority,
        tags=case.tags,
        turns=[
            EvaluationTurn(
                question=turn.question,
                expected_keywords=turn.keyword_anchors,
                expect_images=turn.expect_images,
                expect_no_answer=turn.expect_no_answer,
                min_sources=turn.min_sources,
                min_images=turn.min_images,
                reference_answer=turn.reference_answer,
                required_facts=[fact.model_dump() for fact in turn.required_facts],
                keyword_anchors=turn.keyword_anchors,
                forbidden_facts=turn.forbidden_facts,
                expected_source_ids=turn.expected_source_ids,
                expected_chunk_ids=turn.expected_chunk_ids,
                forbidden_source_ids=turn.forbidden_source_ids,
            )
            for turn in case.turns
        ],
    )


def _legacy_turn_to_spec(raw_turn: dict[str, Any], index: int) -> EvaluationTurnSpec:
    keyword_groups = raw_turn.get("expected_keyword_groups", [])
    required_facts = [
        RequiredFact(id=f"legacy-fact-{index}", text=" / ".join(map(str, group)))
        for index, group in enumerate(keyword_groups, start=1)
        if group
    ]
    return EvaluationTurnSpec(
        question=str(raw_turn["question"]),
        reference_answer=str(raw_turn.get("reference_answer", "")),
        required_facts=required_facts,
        keyword_anchors=[str(item) for item in raw_turn.get("expected_keywords", [])],
        forbidden_facts=[str(item) for item in raw_turn.get("forbidden_facts", [])],
        expect_images=bool(raw_turn.get("expect_images", False)),
        expect_no_answer=bool(raw_turn.get("expect_no_answer", False)),
        min_sources=int(raw_turn.get("min_sources", 0)),
        min_images=int(raw_turn.get("min_images", 0)),
    )


def _legacy_case_to_spec(raw_case: dict[str, Any], index: int) -> EvaluationCaseSpec:
    raw_turns = raw_case.get("turns", [raw_case])
    return EvaluationCaseSpec(
        id=str(raw_case.get("id") or f"case-{index}"),
        category=str(raw_case.get("category") or "未分类"),
        priority=str(raw_case.get("priority") or "P1"),
        tags=[str(tag) for tag in raw_case.get("tags", [])],
        turns=[_legacy_turn_to_spec(turn, turn_index) for turn_index, turn in enumerate(raw_turns, start=1)],
        legacy_unreviewed=True,
    )


def load_evaluation_suite(path: Path) -> EvaluationSuite:
    raw_payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw_payload, dict):
        return EvaluationSuite.model_validate(raw_payload)
    if isinstance(raw_payload, list):
        return EvaluationSuite(
            id="legacy",
            version="legacy",
            description="Legacy evaluation cases pending review.",
            default_thresholds=EvaluationThresholds(
                answer_correctness=0.8,
                faithfulness=0.9,
                p1_required_fact_coverage=0.8,
            ),
            cases=[_legacy_case_to_spec(raw_case, index) for index, raw_case in enumerate(raw_payload, start=1)],
        )
    raise ValueError("评测套件必须是对象或用例列表")
