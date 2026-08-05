from statistics import mean
from uuid import uuid4

from app.evaluation.models import CaseResult, EvaluationRunSummary, MetricStatus


# 计算通过率，避免调用处重复处理空列表除零问题。
def _pass_rate(passed: int, total: int) -> float:
    return passed / total if total else 0.0


# 计算小样本场景下稳定可读的 P95，样本很少时取最大值。
def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(round(len(ordered) * 0.95) - 1, 0)
    return ordered[index]


# 按分类汇总通过率，用于评测中心展示哪个产品模块退化。
def _category_pass_rates(results: list[CaseResult]) -> dict[str, float]:
    grouped: dict[str, list[CaseResult]] = {}
    for result in results:
        grouped.setdefault(result.category, []).append(result)

    return {
        category: _pass_rate(
            sum(1 for result in category_results if result.passed),
            len(category_results),
        )
        for category, category_results in grouped.items()
    }


# 汇总一次评测运行的核心质量和性能指标。
def summarize_case_results(results: list[CaseResult]) -> EvaluationRunSummary:
    case_total = len(results)
    case_passed = sum(1 for result in results if result.passed)
    p0_results = [result for result in results if result.priority == "P0"]
    single_results = [result for result in results if result.case_type == "single"]
    dialogue_results = [result for result in results if result.case_type == "dialogue"]
    latencies = [result.elapsed_ms for result in results]
    faithfulness_scores = [
        turn.faithfulness_score
        for result in results
        for turn in result.turn_results
        if turn.faithfulness_score is not None
    ]
    has_metric_error = any(
        metric.status == MetricStatus.ERROR
        for result in results
        for turn in result.turn_results
        for metric in turn.metric_results
    )

    return EvaluationRunSummary(
        run_id=f"eval-{uuid4().hex}",
        status="INVALID" if has_metric_error else "completed",
        case_total=case_total,
        case_passed=case_passed,
        pass_rate=_pass_rate(case_passed, case_total),
        p0_total=len(p0_results),
        p0_passed=sum(1 for result in p0_results if result.passed),
        avg_latency_ms=mean(latencies) if latencies else 0.0,
        p95_latency_ms=_p95(latencies),
        single_total=len(single_results),
        single_passed=sum(1 for result in single_results if result.passed),
        dialogue_total=len(dialogue_results),
        dialogue_passed=sum(1 for result in dialogue_results if result.passed),
        category_pass_rates=_category_pass_rates(results),
        avg_faithfulness_score=mean(faithfulness_scores) if faithfulness_scores else None,
    )
