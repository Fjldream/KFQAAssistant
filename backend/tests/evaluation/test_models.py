from app.evaluation.models import (
    EvaluationCase,
    EvaluationRunSummary,
    EvaluationTurn,
    RunStatus,
    TurnResult,
    can_transition,
)
import pytest


@pytest.mark.parametrize(("source", "target"), [
    (RunStatus.CREATED, RunStatus.RUNNING),
    (RunStatus.RUNNING, RunStatus.SCORING),
    (RunStatus.SCORING, RunStatus.COMPLETED),
    (RunStatus.RUNNING, RunStatus.INVALID),
    (RunStatus.RUNNING, RunStatus.CANCELLED),
])
def test_allowed_run_transitions(source, target):
    assert can_transition(source, target)


def test_run_cannot_transition_from_terminal_state():
    assert not can_transition(RunStatus.COMPLETED, RunStatus.RUNNING)


def test_run_cannot_cancel_before_it_starts_or_while_scoring():
    assert not can_transition(RunStatus.CREATED, RunStatus.CANCELLED)
    assert not can_transition(RunStatus.SCORING, RunStatus.CANCELLED)


# 验证单轮评测用例在没有显式填写字段时，会使用平台默认值。
def test_evaluation_case_defaults_priority_tags_and_type():
    case = EvaluationCase(
        id="single.editor.areas",
        category="页面编辑器",
        turns=[
            EvaluationTurn(
                question="页面编辑器主要包括哪些区域？",
                expected_keywords=["菜单栏"],
                expected_source_keywords=["页面编辑器"],
            )
        ],
    )

    assert case.priority == "P1"
    assert case.tags == []
    assert case.case_type == "single"


# 验证多轮评测用例会被识别为连续对话类型。
def test_evaluation_case_detects_dialogue_type():
    case = EvaluationCase(
        id="dialog.collect.run",
        category="数采管理",
        turns=[
            EvaluationTurn(question="如何创建采集工程？"),
            EvaluationTurn(question="那怎么运行？"),
        ],
    )

    assert case.case_type == "dialogue"


# 验证评测轮次的规则字段默认是安全的空集合。
def test_evaluation_turn_defaults_rule_fields():
    turn = EvaluationTurn(question="如何运行采集工程？")

    assert turn.expected_keywords == []
    assert turn.expected_keyword_groups == []
    assert turn.expected_source_keywords == []
    assert turn.expected_source_keyword_groups == []
    assert turn.forbidden_source_keywords == []
    assert turn.expect_images is False
    assert turn.expect_no_answer is False
    assert turn.min_sources == 0
    assert turn.min_images == 0


def test_turn_result_faithfulness_defaults():
    turn = TurnResult(question="q", answer="a", standalone_question=None, passed=True,
                      keyword_passed=True, source_passed=True, image_passed=True, no_answer_passed=True)
    assert turn.faithfulness_score is None
    assert turn.faithfulness_claims == []
    assert turn.faithfulness_elapsed_ms == 0.0


def test_turn_result_faithfulness_roundtrip():
    turn = TurnResult(question="q", answer="a", standalone_question=None, passed=True,
                      keyword_passed=True, source_passed=True, image_passed=True, no_answer_passed=True,
                      faithfulness_score=0.5, faithfulness_claims=[{"claim": "c", "supported": False, "evidence": ""}],
                      faithfulness_elapsed_ms=123.0)
    assert turn.faithfulness_score == 0.5
    assert turn.faithfulness_claims[0]["supported"] is False


def test_run_summary_faithfulness_and_kb_fields():
    summary = EvaluationRunSummary(run_id="r", status="completed", case_total=1, case_passed=1, pass_rate=1.0)
    assert summary.avg_faithfulness_score is None
    assert summary.knowledge_base_id is None


def test_case_knowledge_base_id():
    case = EvaluationCase(id="c", category="cat", turns=[EvaluationTurn(question="q")], knowledge_base_id="kb-1")
    assert case.knowledge_base_id == "kb-1"
