from scripts.load_test import LoadTestResult, format_report, percentile, summarize_results


# 验证百分位计算会按耗时排序并返回上取整位置的值。
def test_percentile_uses_sorted_upper_rank():
    assert percentile([300.0, 100.0, 200.0], 95) == 300.0
    assert percentile([], 95) == 0.0


# 验证压测结果汇总会统计成功率、失败数和耗时指标。
def test_summarize_results_calculates_success_rate_and_latency():
    results = [
        LoadTestResult(success=True, elapsed_ms=100.0, status_code=200, error=""),
        LoadTestResult(success=True, elapsed_ms=300.0, status_code=200, error=""),
        LoadTestResult(success=False, elapsed_ms=500.0, status_code=500, error="server error"),
    ]

    summary = summarize_results(results)

    assert summary["total"] == 3
    assert summary["success"] == 2
    assert summary["failed"] == 1
    assert summary["success_rate"] == 2 / 3
    assert summary["avg_ms"] == 300.0
    assert summary["p95_ms"] == 500.0


# 验证压测报告会输出适合命令行阅读的中文摘要。
def test_format_report_outputs_chinese_summary():
    report = format_report(
        {
            "total": 2,
            "success": 1,
            "failed": 1,
            "success_rate": 0.5,
            "avg_ms": 120.0,
            "p95_ms": 200.0,
            "min_ms": 80.0,
            "max_ms": 200.0,
        }
    )

    assert "请求数: 2" in report
    assert "成功率: 50%" in report
    assert "P95耗时: 200ms" in report
