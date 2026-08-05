from app.evaluation.answer_quality import evaluate_answer_quality
from app.evaluation.judge import JudgementCompletion, JudgementError
from app.evaluation.models import MetricStatus
from app.evaluation.suite import EvaluationTurnSpec, RequiredFact


class FakeJudge:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def complete_json(self, system_prompt, user_prompt):
        self.calls.append((system_prompt, user_prompt))
        if isinstance(self.response, Exception):
            raise self.response
        return JudgementCompletion(self.response)


def turn_spec(priority="P1"):
    return EvaluationTurnSpec(
        question="如何创建工程？",
        reference_answer="进入数采管理后创建工程并填写名称。",
        required_facts=[
            RequiredFact(id="entry", text="进入数采管理"),
            RequiredFact(id="name", text="填写名称"),
        ],
    )


def metric_by_name(results, name):
    return next(result for result in results if result.name == name)


def test_answer_quality_reports_missing_required_fact():
    judge = FakeJudge({
        "correctness": 0.75,
        "relevance": 1.0,
        "facts": [{"id": "entry", "covered": True}, {"id": "name", "covered": False}],
        "forbidden_fact_matches": [],
    })

    results = evaluate_answer_quality(judge, turn_spec(), "进入数采管理后创建工程。")

    coverage = metric_by_name(results, "required_fact_coverage")
    assert coverage.score == 0.5
    assert coverage.status == MetricStatus.FAILED
    assert coverage.details["missing_fact_ids"] == ["name"]


def test_answer_quality_reports_forbidden_fact_match():
    spec = turn_spec()
    spec.forbidden_facts = ["工程会自动运行"]
    judge = FakeJudge({
        "correctness": 1.0,
        "relevance": 1.0,
        "facts": [{"id": "entry", "covered": True}, {"id": "name", "covered": True}],
        "forbidden_fact_matches": ["工程会自动运行"],
    })

    forbidden = metric_by_name(evaluate_answer_quality(judge, spec, "答案"), "forbidden_fact_matches")

    assert forbidden.score == 0.0
    assert forbidden.status == MetricStatus.FAILED


def test_answer_quality_returns_error_for_malformed_judge_output():
    judge = FakeJudge({"correctness": 1.2, "relevance": 1.0, "facts": [], "forbidden_fact_matches": []})

    results = evaluate_answer_quality(judge, turn_spec(), "答案")

    assert {result.status for result in results} == {MetricStatus.ERROR}
    assert {result.error_code for result in results} == {"judge_schema_error"}


def test_answer_quality_returns_stable_http_error():
    results = evaluate_answer_quality(FakeJudge(JudgementError()), turn_spec(), "答案")

    assert {result.error_code for result in results} == {"judge_http_error"}


def test_answer_quality_skips_semantic_metrics_for_refusal():
    results = evaluate_answer_quality(FakeJudge({}), turn_spec(), "手册中没有找到相关说明。")

    assert {result.status for result in results} == {MetricStatus.SKIPPED}
