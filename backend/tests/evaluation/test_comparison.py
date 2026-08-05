from app.evaluation.comparison import compare_case_results
from app.evaluation.gates import GateThresholds, evaluate_regression_gate
from app.evaluation.models import CaseResult, EvaluationRunDetail, EvaluationRunSummary, GateOutcome, GateResult, MetricResult, MetricStatus, TurnResult
from pytest import approx


# 构造最小轮次结果，用于对比测试。
def _turn(passed: bool) -> TurnResult:
    return TurnResult(
        question="问题",
        answer="回答",
        standalone_question="独立问题",
        passed=passed,
        keyword_passed=passed,
        source_passed=passed,
        image_passed=passed,
        no_answer_passed=passed,
    )


# 构造最小用例结果，用于观察两次运行之间的状态变化。
def _case(case_id: str, passed: bool, priority: str = "P1") -> CaseResult:
    return CaseResult(
        case_id=case_id,
        category="数采管理",
        priority=priority,
        case_type="single",
        passed=passed,
        turn_results=[_turn(passed)],
    )


# 验证历史对比能识别新增失败、新增通过、持续失败和通过率变化。
def test_compare_case_results_reports_status_changes_and_delta():
    baseline = [_case("case-1", True), _case("case-2", False), _case("case-3", False)]
    current = [_case("case-1", False), _case("case-2", True), _case("case-3", False), _case("case-4", True)]

    result = compare_case_results(current=current, baseline=baseline)

    assert result.regressed_case_ids == ["case-1"]
    assert result.recovered_case_ids == ["case-2"]
    assert result.unchanged_failed_case_ids == ["case-3"]
    assert result.new_case_ids == ["case-4"]
    assert result.pass_rate_delta == approx(1 / 6)


def _summary(**overrides) -> EvaluationRunSummary:
    values = {
        "run_id": "run",
        "status": "completed",
        "case_total": 20,
        "case_passed": 20,
        "pass_rate": 1.0,
        "p0_total": 1,
        "p0_passed": 1,
        "completed_count": 20,
        "judge_coverage": 1.0,
        "p95_latency_ms": 1000.0,
    }
    values.update(overrides)
    return EvaluationRunSummary(**values)


def _detail(summary: EvaluationRunSummary, cases: list[CaseResult]) -> EvaluationRunDetail:
    return EvaluationRunDetail(summary=summary, gate_result=GateResult(passed=True), case_results=cases)


def test_regression_gate_fails_for_p0_case_regression():
    current = _detail(_summary(), [_case("p0", False, priority="P0")])
    baseline = _detail(_summary(), [_case("p0", True, priority="P0")])

    decision = evaluate_regression_gate(current, baseline, GateThresholds())

    assert decision.outcome == GateOutcome.FAILED
    assert "P0" in decision.regression_reasons[0]


def test_regression_gate_fails_for_new_severe_hallucination():
    current_case = _case("case-1", False)
    current_case.turn_results[0].metric_results.append(
        MetricResult("forbidden_fact_matches", 0.0, MetricStatus.FAILED)
    )
    decision = evaluate_regression_gate(
        _detail(_summary(), [current_case]),
        _detail(_summary(), [_case("case-1", True)]),
        GateThresholds(),
    )

    assert decision.outcome == GateOutcome.FAILED
    assert "严重幻觉" in decision.regression_reasons[0]


def test_regression_gate_fails_when_pass_rate_drops_more_than_five_points():
    decision = evaluate_regression_gate(
        _detail(_summary(pass_rate=0.94), []),
        _detail(_summary(pass_rate=1.0), []),
        GateThresholds(),
    )

    assert decision.outcome == GateOutcome.FAILED
    assert "通过率" in decision.regression_reasons[0]


def test_regression_gate_fails_when_p95_exceeds_relative_or_absolute_cap():
    decision = evaluate_regression_gate(
        _detail(_summary(p95_latency_ms=1251), []),
        _detail(_summary(p95_latency_ms=1000), []),
        GateThresholds(max_p95_latency_ms=2000),
    )

    assert decision.outcome == GateOutcome.FAILED
    assert "P95" in decision.regression_reasons[0]


def test_regression_gate_fails_when_positive_p95_exceeds_zero_baseline_limit():
    decision = evaluate_regression_gate(
        _detail(_summary(p95_latency_ms=1), []),
        _detail(_summary(p95_latency_ms=0), []),
        GateThresholds(),
    )

    assert decision.outcome == GateOutcome.FAILED
    assert "P95" in decision.regression_reasons[0]


def test_regression_gate_invalidates_an_invalid_baseline():
    decision = evaluate_regression_gate(
        _detail(_summary(), []),
        _detail(_summary(judge_coverage=0.0), []),
        GateThresholds(),
    )

    assert decision.outcome == GateOutcome.INVALID
    assert decision.validity_reasons
