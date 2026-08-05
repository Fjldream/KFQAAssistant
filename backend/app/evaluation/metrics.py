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


def _average_metric(results: list[CaseResult], name: str) -> float | None:
    scores = [
        metric.score
        for result in results
        for turn in result.turn_results
        for metric in turn.metric_results
        if metric.name == name and metric.score is not None
    ]
    return mean(scores) if scores else None


def _token_count(token_usage: object) -> int:
    if token_usage is None:
        return 0
    if isinstance(token_usage, dict):
        return int(token_usage.get("total_tokens", token_usage.get("total", 0)) or 0)
    return int(getattr(token_usage, "total_tokens", getattr(token_usage, "total", 0)) or 0)


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
    single_latencies = [result.elapsed_ms for result in single_results]
    dialogue_latencies = [result.elapsed_ms for result in dialogue_results]
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
    metric_results = [
        metric
        for result in results
        for turn in result.turn_results
        for metric in turn.metric_results
    ]
    judge_metrics = [
        metric for metric in metric_results
        if metric.name in {"answer_correctness", "answer_relevance", "required_fact_coverage", "forbidden_fact_matches", "faithfulness"}
        and metric.status != MetricStatus.SKIPPED
    ]
    judge_completed = sum(1 for metric in judge_metrics if metric.status in {MetricStatus.PASSED, MetricStatus.FAILED})

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
        avg_faithfulness_score=(
            mean(faithfulness_scores)
            if faithfulness_scores
            else _average_metric(results, "faithfulness")
        ),
        completed_count=case_total,
        error_count=sum(1 for metric in metric_results if metric.status == MetricStatus.ERROR),
        judge_coverage=judge_completed / len(judge_metrics) if judge_metrics else 0.0,
        avg_correctness_score=_average_metric(results, "answer_correctness"),
        avg_fact_coverage_score=_average_metric(results, "required_fact_coverage"),
        avg_retrieval_recall=_average_metric(results, "recall_at_k"),
        avg_retrieval_mrr=_average_metric(results, "mrr"),
        single_p95_latency_ms=_p95(single_latencies),
        dialogue_p95_latency_ms=_p95(dialogue_latencies),
        total_token_count=sum(_token_count(metric.token_usage) for metric in metric_results),
        estimated_cost=sum(float(metric.details.get("estimated_cost", 0.0) or 0.0) for metric in metric_results),
    )
