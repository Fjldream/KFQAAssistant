from app.evaluation.gates import (
    GateThresholds,
    evaluate_absolute_gate,
    evaluate_gates,
    evaluate_run_validity,
)
from app.evaluation.models import EvaluationRunSummary, GateOutcome, GateMode


# 构造评测汇总，方便门禁测试只关注上线规则。
def _summary(
    pass_rate: float = 1.0,
    p0_total: int = 1,
    p0_passed: int = 1,
    p95_latency_ms: float = 1000,
) -> EvaluationRunSummary:
    return EvaluationRunSummary(
        run_id="run-1",
        status="completed",
        case_total=1,
        case_passed=1 if pass_rate == 1 else 0,
        pass_rate=pass_rate,
        p0_total=p0_total,
        p0_passed=p0_passed,
        p95_latency_ms=p95_latency_ms,
    )


# 验证通过率低于阈值时门禁失败。
def test_gate_fails_when_pass_rate_below_threshold():
    result = evaluate_gates(_summary(pass_rate=0.7), fail_under=0.8, max_p95_ms=None)

    assert result.passed is False
    assert "通过率 70.00% 低于阈值 80.00%" in result.reasons


# 验证 P0 用例没有全部通过时门禁失败。
def test_gate_fails_when_p0_case_fails():
    result = evaluate_gates(_summary(p0_total=2, p0_passed=1), fail_under=0.8, max_p95_ms=None)

    assert result.passed is False
    assert "P0 用例未全部通过：1/2" in result.reasons


# 验证 P95 耗时超过阈值时门禁失败。
def test_gate_fails_when_p95_exceeds_threshold():
    result = evaluate_gates(_summary(p95_latency_ms=31000), fail_under=0.8, max_p95_ms=30000)

    assert result.passed is False
    assert "P95 耗时 31000ms 超过阈值 30000ms" in result.reasons


# 验证所有规则满足时门禁通过。
def test_gate_passes_when_all_rules_satisfy():
    result = evaluate_gates(_summary(), fail_under=0.8, max_p95_ms=30000)

    assert result.passed is True
    assert result.reasons == []


def _release_summary(**overrides) -> EvaluationRunSummary:
    values = {
        "run_id": "release-1",
        "status": "completed",
        "case_total": 20,
        "case_passed": 20,
        "pass_rate": 1.0,
        "p0_total": 2,
        "p0_passed": 2,
        "completed_count": 20,
        "judge_coverage": 1.0,
        "avg_correctness_score": 0.9,
        "avg_fact_coverage_score": 0.9,
        "avg_faithfulness_score": 0.95,
        "p95_latency_ms": 1000.0,
    }
    values.update(overrides)
    return EvaluationRunSummary(**values)


def test_run_is_invalid_when_judge_coverage_is_incomplete():
    decision = evaluate_run_validity(_release_summary(judge_coverage=0.95))

    assert decision.outcome == GateOutcome.INVALID
    assert decision.validity_reasons


def test_run_is_invalid_when_judge_coverage_has_no_samples():
    decision = evaluate_run_validity(_release_summary(judge_coverage=0.0))

    assert decision.outcome == GateOutcome.INVALID


def test_absolute_gate_fails_each_non_compensating_quality_threshold():
    decision = evaluate_absolute_gate(
        _release_summary(pass_rate=0.84, p0_passed=1, avg_faithfulness_score=0.89),
        GateThresholds(),
    )

    assert decision.outcome == GateOutcome.FAILED
    assert len(decision.absolute_reasons) == 3


def test_calibration_quality_failures_are_non_blocking_only_after_validity_passes():
    decision = evaluate_absolute_gate(
        _release_summary(pass_rate=0.84),
        GateThresholds(mode=GateMode.CALIBRATION),
    )

    assert decision.outcome == GateOutcome.PASSED
    assert decision.absolute_reasons
