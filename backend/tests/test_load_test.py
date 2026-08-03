import asyncio
import importlib
import json
from pathlib import Path

import httpx

from scripts.load_test import LoadTestResult, format_report, percentile, run_one_request, summarize_results, write_json_report


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


def test_summarize_results_includes_percentiles_throughput_and_status_codes():
    results = [
        LoadTestResult(success=True, elapsed_ms=10.0, status_code=200, error=""),
        LoadTestResult(success=True, elapsed_ms=20.0, status_code=200, error=""),
        LoadTestResult(success=False, elapsed_ms=100.0, status_code=500, error="server error"),
    ]

    summary = summarize_results(results, duration_seconds=0.2)

    assert summary["p50_ms"] == 20.0
    assert summary["p95_ms"] == 100.0
    assert summary["p99_ms"] == 100.0
    assert summary["status_codes"] == {"200": 2, "500": 1}
    assert summary["throughput_rps"] == 15.0


def test_run_one_request_sends_api_key_only_when_configured():
    received_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        received_headers.append(request.headers.get("X-API-Key"))
        return httpx.Response(200, json={"status": "ok"})

    async def run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            await run_one_request(client, "http://example.test/api/chat", "问题", api_key="secret")
            await run_one_request(client, "http://example.test/api/chat", "问题")

    asyncio.run(run())

    assert received_headers == ["secret", None]


def test_write_json_report_does_not_add_api_key(tmp_path: Path):
    output_file = tmp_path / "reports" / "load-test.json"

    write_json_report(output_file, {"summary": {"success": 1}})

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["summary"]["success"] == 1
    assert "secret" not in output_file.read_text(encoding="utf-8")


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


# 验证压测脚本会读取 .env 中的接口地址，和 .env.example 的使用方式保持一致。
def test_load_test_default_api_url_reads_dotenv(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KF_RAG_API_URL", raising=False)
    Path(".env").write_text("KF_RAG_API_URL=http://example.test/api/chat\n", encoding="utf-8")

    import scripts.load_test as load_test

    reloaded = importlib.reload(load_test)

    assert reloaded.DEFAULT_API_URL == "http://example.test/api/chat"
