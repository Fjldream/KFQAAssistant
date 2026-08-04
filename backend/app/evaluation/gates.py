from app.evaluation.models import EvaluationRunSummary, GateResult


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
