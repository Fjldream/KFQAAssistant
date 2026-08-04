from app.evaluation.comparison import compare_case_results
from app.evaluation.models import CaseResult, TurnResult
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
def _case(case_id: str, passed: bool) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        category="数采管理",
        priority="P1",
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
