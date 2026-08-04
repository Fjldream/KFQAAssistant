from app.evaluation.models import CaseResult, ComparisonResult


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
