from app.evaluation.metrics import summarize_case_results
from app.evaluation.models import CaseResult, TurnResult


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
