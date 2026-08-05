from app.evaluation.gates import evaluate_run_validity
from app.evaluation.metrics import summarize_case_results
from app.evaluation.models import GateOutcome
from app.evaluation.models import CaseResult, MetricResult, MetricStatus, TurnResult


# 构造最小轮次结果，方便指标测试聚焦在汇总逻辑。
def _turn(passed: bool = True, elapsed_ms: float = 100.0) -> TurnResult:
    return TurnResult(
        question="问题",
        answer="回答",
        standalone_question="独立问题",
        passed=passed,
        keyword_passed=passed,
        source_passed=passed,
        image_passed=passed,
        no_answer_passed=passed,
        elapsed_ms=elapsed_ms,
    )


# 构造最小用例结果，避免每个测试重复铺大量字段。
def _case(
    case_id: str,
    passed: bool,
    category: str = "数采管理",
    priority: str = "P1",
    case_type: str = "single",
    elapsed_ms: float = 100.0,
) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        category=category,
        priority=priority,
        case_type=case_type,
        passed=passed,
        turn_results=[_turn(passed=passed, elapsed_ms=elapsed_ms)],
        elapsed_ms=elapsed_ms,
    )


# 验证评测运行会汇总整体通过率、P0 通过数、分类通过率和单轮/多轮通过率。
def test_summarize_case_results_calculates_pass_rates_and_counts():
    summary = summarize_case_results(
        [
            _case("case-1", True, category="数采管理", priority="P0", case_type="single", elapsed_ms=100),
            _case("case-2", False, category="数采管理", priority="P0", case_type="dialogue", elapsed_ms=300),
            _case("case-3", True, category="页面编辑器", priority="P1", case_type="single", elapsed_ms=200),
        ]
    )

    assert summary.case_total == 3
    assert summary.case_passed == 2
    assert summary.pass_rate == 2 / 3
    assert summary.p0_total == 2
    assert summary.p0_passed == 1
    assert summary.category_pass_rates == {"数采管理": 0.5, "页面编辑器": 1.0}
    assert summary.single_total == 2
    assert summary.single_passed == 2
    assert summary.dialogue_total == 1
    assert summary.dialogue_passed == 0
    assert summary.avg_latency_ms == 200
    assert summary.p95_latency_ms == 300


# 验证空结果不会产生除零错误。
def test_summarize_case_results_handles_empty_results():
    summary = summarize_case_results([])

    assert summary.case_total == 0
    assert summary.case_passed == 0
    assert summary.pass_rate == 0
    assert summary.category_pass_rates == {}


def test_summarize_case_results_marks_judge_metric_error_invalid():
    result = CaseResult(
        case_id="judge-error",
        category="测试",
        priority="P1",
        case_type="single",
        passed=False,
        turn_results=[TurnResult(
            question="q", answer="a", standalone_question=None, passed=False,
            keyword_passed=True, source_passed=True, image_passed=True, no_answer_passed=True,
            metric_results=[MetricResult("answer_correctness", None, MetricStatus.ERROR, error_code="judge_http_error")],
        )],
    )

    summary = summarize_case_results([result])

    assert summary.status == "INVALID"


def test_summarize_case_results_includes_gate_metrics_and_run_counts():
    result = CaseResult(
        case_id="metrics",
        category="测试",
        priority="P1",
        case_type="single",
        passed=True,
        elapsed_ms=200.0,
        turn_results=[TurnResult(
            question="q", answer="a", standalone_question=None, passed=True,
            keyword_passed=True, source_passed=True, image_passed=True, no_answer_passed=True,
            metric_results=[
                MetricResult("answer_correctness", 0.8, MetricStatus.PASSED),
                MetricResult("required_fact_coverage", 0.9, MetricStatus.PASSED),
                MetricResult("faithfulness", 1.0, MetricStatus.PASSED),
                MetricResult("recall_at_k", 0.7, MetricStatus.FAILED),
                MetricResult("mrr", 0.6, MetricStatus.FAILED),
            ],
        )],
    )

    summary = summarize_case_results([result])

    assert summary.completed_count == 1
    assert summary.error_count == 0
    assert summary.judge_coverage == 1.0
    assert summary.avg_correctness_score == 0.8
    assert summary.avg_fact_coverage_score == 0.9
    assert summary.avg_faithfulness_score == 1.0
    assert summary.avg_retrieval_recall == 0.7
    assert summary.avg_retrieval_mrr == 0.6
    assert summary.single_p95_latency_ms == 200.0
    assert summary.dialogue_p95_latency_ms == 0.0


def test_summarize_case_results_marks_missing_required_judge_dimensions_invalid():
    result = _case("missing-judge-metrics", True)
    result.turn_results[0].metric_results.append(
        MetricResult("answer_correctness", 0.9, MetricStatus.PASSED)
    )

    summary = summarize_case_results([result])

    assert summary.judge_coverage == 1 / 3
    assert summary.missing_judge_metrics == ["faithfulness", "required_fact_coverage"]
    assert evaluate_run_validity(summary).outcome == GateOutcome.INVALID


def test_summarize_case_results_marks_scoreless_required_judge_metric_invalid():
    result = _case("scoreless-judge-metric", True)
    result.turn_results[0].metric_results.extend([
        MetricResult("answer_correctness", 0.9, MetricStatus.PASSED),
        MetricResult("required_fact_coverage", 0.9, MetricStatus.PASSED),
        MetricResult("faithfulness", None, MetricStatus.PASSED),
    ])

    summary = summarize_case_results([result])

    assert summary.judge_coverage == 2 / 3
    assert summary.missing_judge_metrics == ["faithfulness"]
    assert evaluate_run_validity(summary).outcome == GateOutcome.INVALID


def test_summarize_case_results_treats_valid_refusal_judge_skips_as_covered():
    result = _case("intentional-refusal", True)
    result.turn_results[0].metric_results.extend([
        MetricResult("answer_correctness", None, MetricStatus.SKIPPED),
        MetricResult("required_fact_coverage", None, MetricStatus.SKIPPED),
        MetricResult("faithfulness", None, MetricStatus.SKIPPED),
    ])

    summary = summarize_case_results([result])

    assert summary.judge_coverage == 1.0
    assert summary.missing_judge_metrics == []
    assert evaluate_run_validity(summary).outcome == GateOutcome.PASSED


def test_summarize_empty_run_is_invalid():
    assert evaluate_run_validity(summarize_case_results([])).outcome == GateOutcome.INVALID
