from dataclasses import dataclass

from app.evaluation.comparison import compare_run_summaries
from app.evaluation.models import (
    EvaluationRunDetail,
    EvaluationRunSummary,
    GateDecision,
    GateMode,
    GateOutcome,
    GateResult,
    RunStatus,
)


@dataclass(frozen=True)
class GateThresholds:
    mode: GateMode = GateMode.BLOCKING
    min_pass_rate: float = 0.85
    min_avg_correctness_score: float = 0.8
    min_avg_fact_coverage_score: float = 0.8
    min_avg_faithfulness_score: float = 0.9
    max_p95_latency_ms: float | None = 30_000.0
    max_pass_rate_drop: float = 0.05
    max_p95_increase_ratio: float = 1.25


def evaluate_run_validity(summary: EvaluationRunSummary) -> GateDecision:
    reasons: list[str] = []
    if summary.case_total == 0:
        reasons.append("评测运行没有用例，无法形成有效结论")
    if summary.completed_count != summary.case_total:
        reasons.append(f"评测用例未全部完成：{summary.completed_count}/{summary.case_total}")
    if summary.error_count:
        reasons.append(f"评测存在指标错误：{summary.error_count}")
    if summary.judge_coverage <= 0:
        reasons.append("Judge 指标覆盖率为 0，无法验证质量")
    elif summary.judge_coverage < 1:
        reasons.append(f"Judge 指标覆盖不完整：{summary.judge_coverage:.2%}")
    if summary.status == RunStatus.INVALID or summary.status == RunStatus.INVALID.value:
        reasons.append("评测运行已标记为 INVALID")
    return GateDecision(
        outcome=GateOutcome.INVALID if reasons else GateOutcome.PASSED,
        validity_reasons=reasons,
    )


def evaluate_absolute_gate(summary: EvaluationRunSummary, thresholds: GateThresholds) -> GateDecision:
    validity = evaluate_run_validity(summary)
    if validity.outcome == GateOutcome.INVALID:
        return validity

    reasons: list[str] = []
    if summary.pass_rate < thresholds.min_pass_rate:
        reasons.append(f"通过率 {summary.pass_rate:.2%} 低于阈值 {thresholds.min_pass_rate:.2%}")
    if summary.p0_passed < summary.p0_total:
        reasons.append(f"P0 用例未全部通过：{summary.p0_passed}/{summary.p0_total}")
    for score, minimum, label in (
        (summary.avg_correctness_score, thresholds.min_avg_correctness_score, "平均正确性"),
        (summary.avg_fact_coverage_score, thresholds.min_avg_fact_coverage_score, "平均事实覆盖率"),
        (summary.avg_faithfulness_score, thresholds.min_avg_faithfulness_score, "平均忠实度"),
    ):
        if score is not None and score < minimum:
            reasons.append(f"{label} {score:.2%} 低于阈值 {minimum:.2%}")
    if thresholds.max_p95_latency_ms is not None and summary.p95_latency_ms > thresholds.max_p95_latency_ms:
        reasons.append(f"P95 耗时 {summary.p95_latency_ms:.0f}ms 超过阈值 {thresholds.max_p95_latency_ms:.0f}ms")

    return GateDecision(
        outcome=GateOutcome.FAILED if reasons and thresholds.mode == GateMode.BLOCKING else GateOutcome.PASSED,
        absolute_reasons=reasons,
    )


def evaluate_regression_gate(
    current: EvaluationRunDetail,
    baseline: EvaluationRunDetail,
    thresholds: GateThresholds,
) -> GateDecision:
    validity = evaluate_run_validity(current.summary)
    if validity.outcome == GateOutcome.INVALID:
        return validity

    comparison = compare_run_summaries(
        current.summary,
        baseline.summary,
        current.case_results,
        baseline.case_results,
    )
    reasons = list(comparison.case_regression_reasons)
    if comparison.pass_rate_delta < -thresholds.max_pass_rate_drop:
        reasons.append(f"通过率下降 {-comparison.pass_rate_delta:.2%}，超过阈值 {thresholds.max_pass_rate_drop:.2%}")
    if baseline.summary.p95_latency_ms > 0:
        p95_limit = baseline.summary.p95_latency_ms * thresholds.max_p95_increase_ratio
        if thresholds.max_p95_latency_ms is not None:
            p95_limit = min(p95_limit, thresholds.max_p95_latency_ms)
        if current.summary.p95_latency_ms > p95_limit:
            reasons.append(f"P95 耗时 {current.summary.p95_latency_ms:.0f}ms 超过回归阈值 {p95_limit:.0f}ms")

    return GateDecision(
        outcome=GateOutcome.FAILED if reasons and thresholds.mode == GateMode.BLOCKING else GateOutcome.PASSED,
        regression_reasons=reasons,
    )


# 根据评测汇总指标判断本次运行是否满足上线质量门禁。
def evaluate_gates(
    summary: EvaluationRunSummary,
    fail_under: float,
    max_p95_ms: float | None,
) -> GateResult:
    reasons: list[str] = []

    if summary.pass_rate < fail_under:
        reasons.append(f"通过率 {summary.pass_rate:.2%} 低于阈值 {fail_under:.2%}")

    if summary.p0_passed < summary.p0_total:
        reasons.append(f"P0 用例未全部通过：{summary.p0_passed}/{summary.p0_total}")

    if max_p95_ms is not None and summary.p95_latency_ms > max_p95_ms:
        reasons.append(f"P95 耗时 {summary.p95_latency_ms:.0f}ms 超过阈值 {max_p95_ms:.0f}ms")

    return GateResult(passed=not reasons, reasons=reasons)
