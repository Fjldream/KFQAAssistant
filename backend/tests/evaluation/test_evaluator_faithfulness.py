from app.evaluation.evaluator import evaluate_case
from app.evaluation.metrics_registry import METRIC_REGISTRY
from app.evaluation.models import EvaluationCase, EvaluationTurn, MetricStatus
from app.schemas.chat import ChatResponse, SourceSnippet


class FakeChain:
    def __init__(self, response: ChatResponse):
        self.response = response

    def answer(self, question, conversation_summary="", conversation_turn_count=0, recent_messages=None):
        return self.response


class FakeJudge:
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {"claims": [{"claim": "声明一", "supported": True, "evidence": "依据"}]}


def _make_case() -> EvaluationCase:
    return EvaluationCase(
        id="c1",
        category="cat",
        turns=[EvaluationTurn(question="问题？")],
    )


def test_evaluate_case_records_faithfulness():
    chain = FakeChain(ChatResponse(
        answer="按钮可以配置颜色。",
        sources=[SourceSnippet(title="t", source_path="p.md", snippet="按钮可以配置颜色。", evidence_ids=["资料 1"], images=[], score=0.9)],
    ))
    case_result = evaluate_case(chain, _make_case(), judge=FakeJudge(), semantic_enabled=True, metrics=("faithfulness",))
    turn = case_result.turn_results[0]
    assert turn.faithfulness_score == 1.0
    assert turn.faithfulness_claims == [{"claim": "声明一", "supported": True, "evidence": "依据"}]


def test_evaluate_case_skips_faithfulness_for_no_answer():
    chain = FakeChain(ChatResponse(answer="手册中没有找到相关说明。", sources=[]))
    case_result = evaluate_case(chain, _make_case(), judge=FakeJudge(), semantic_enabled=True, metrics=("faithfulness",))
    turn = case_result.turn_results[0]
    assert turn.faithfulness_score is None
    assert turn.faithfulness_claims == []


def test_evaluate_case_disabled_leaves_faithfulness_none():
    chain = FakeChain(ChatResponse(answer="按钮可以配置颜色。", sources=[SourceSnippet(title="t", source_path="p.md", snippet="s", evidence_ids=["资料 1"], images=[], score=0.9)]))
    case_result = evaluate_case(chain, _make_case(), judge=FakeJudge(), semantic_enabled=False, metrics=("faithfulness",))
    turn = case_result.turn_results[0]
    assert turn.faithfulness_score is None
    assert turn.faithfulness_claims == []


def test_evaluate_case_without_judge_marks_configured_judge_metric_error():
    chain = FakeChain(ChatResponse(
        answer="按钮可以配置颜色。",
        sources=[SourceSnippet(title="t", source_path="p.md", snippet="s", evidence_ids=["资料 1"], images=[], score=0.9)],
    ))
    case_result = evaluate_case(chain, _make_case(), semantic_enabled=True, metrics=("faithfulness",))
    turn = case_result.turn_results[0]
    assert turn.faithfulness_score is None
    assert turn.faithfulness_claims == []
    assert turn.metric_results[0].status == MetricStatus.ERROR
    assert turn.metric_results[0].error_code == "judge_unavailable"
    assert case_result.passed is False
