from app.evaluation.models import CaseResult, ComparisonResult, EvaluationRunSummary, MetricStatus


# 计算一组用例结果的通过率，供历史运行对比使用。
def _pass_rate(results: list[CaseResult]) -> float:
    if not results:
        return 0.0
    return sum(1 for result in results if result.passed) / len(results)


# 对比当前运行和基准运行，识别退化、恢复、持续失败、新增和移除用例。
def compare_case_results(
    current: list[CaseResult],
    baseline: list[CaseResult],
) -> ComparisonResult:
    current_by_id = {result.case_id: result for result in current}
    baseline_by_id = {result.case_id: result for result in baseline}
    shared_ids = sorted(current_by_id.keys() & baseline_by_id.keys())

    regressed_case_ids = [
        case_id for case_id in shared_ids if baseline_by_id[case_id].passed and not current_by_id[case_id].passed
    ]
    recovered_case_ids = [
        case_id for case_id in shared_ids if not baseline_by_id[case_id].passed and current_by_id[case_id].passed
    ]
    unchanged_failed_case_ids = [
        case_id for case_id in shared_ids if not baseline_by_id[case_id].passed and not current_by_id[case_id].passed
    ]

    return ComparisonResult(
        regressed_case_ids=regressed_case_ids,
        recovered_case_ids=recovered_case_ids,
        unchanged_failed_case_ids=unchanged_failed_case_ids,
        new_case_ids=sorted(current_by_id.keys() - baseline_by_id.keys()),
        removed_case_ids=sorted(baseline_by_id.keys() - current_by_id.keys()),
        pass_rate_delta=_pass_rate(current) - _pass_rate(baseline),
    )


def compare_run_summaries(
    current: EvaluationRunSummary,
    baseline: EvaluationRunSummary,
    current_cases: list[CaseResult],
    baseline_cases: list[CaseResult],
) -> ComparisonResult:
    comparison = compare_case_results(current_cases, baseline_cases)
    metric_names = (
        "pass_rate",
        "avg_correctness_score",
        "avg_fact_coverage_score",
        "avg_faithfulness_score",
        "avg_retrieval_recall",
        "avg_retrieval_mrr",
        "p95_latency_ms",
        "single_p95_latency_ms",
        "dialogue_p95_latency_ms",
        "total_token_count",
        "estimated_cost",
    )
    metric_deltas = {
        name: float(getattr(current, name)) - float(getattr(baseline, name))
        for name in metric_names
        if getattr(current, name) is not None and getattr(baseline, name) is not None
    }
    current_by_id = {case.case_id: case for case in current_cases}
    baseline_by_id = {case.case_id: case for case in baseline_cases}
    case_reasons = [
        f"P0 用例退化：{case_id}"
        for case_id in comparison.regressed_case_ids
        if current_by_id[case_id].priority == "P0"
    ]
    for case_id, case in sorted(current_by_id.items()):
        prior = baseline_by_id.get(case_id)
        current_has_hallucination = any(
            metric.name == "forbidden_fact_matches" and metric.status == MetricStatus.FAILED
            for turn in case.turn_results
            for metric in turn.metric_results
        )
        baseline_has_hallucination = prior is not None and any(
            metric.name == "forbidden_fact_matches" and metric.status == MetricStatus.FAILED
            for turn in prior.turn_results
            for metric in turn.metric_results
        )
        if current_has_hallucination and not baseline_has_hallucination:
            case_reasons.append(f"新增严重幻觉：{case_id}")

    return ComparisonResult(
        regressed_case_ids=comparison.regressed_case_ids,
        recovered_case_ids=comparison.recovered_case_ids,
        unchanged_failed_case_ids=comparison.unchanged_failed_case_ids,
        new_case_ids=comparison.new_case_ids,
        removed_case_ids=comparison.removed_case_ids,
        pass_rate_delta=current.pass_rate - baseline.pass_rate,
        metric_deltas=metric_deltas,
        case_regression_reasons=case_reasons,
    )
