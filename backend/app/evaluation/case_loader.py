import json
from pathlib import Path
from typing import Any

from app.evaluation.models import EvaluationCase, EvaluationTurn


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
    return [_parse_case(raw_case, index) for index, raw_case in enumerate(raw_cases, start=1)]
