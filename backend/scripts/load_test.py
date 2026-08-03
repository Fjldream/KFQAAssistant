import argparse
import asyncio
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import httpx
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path.cwd() / ".env")
DEFAULT_API_URL = os.getenv("KF_RAG_API_URL", "http://127.0.0.1:8000/api/chat")
DEFAULT_QUESTION = "页面编辑器主要包括哪些区域？"


@dataclass(frozen=True)
class LoadTestResult:
    success: bool
    elapsed_ms: float
    status_code: int | None
    error: str


# 计算指定百分位耗时，使用上取整位置，便于观察慢请求。
def percentile(values: list[float], percent: int) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = max(math.ceil(len(sorted_values) * percent / 100) - 1, 0)
    return sorted_values[index]


# 汇总压测结果，计算成功率、百分位耗时、吞吐量和状态码分布。
def summarize_results(
    results: list[LoadTestResult],
    duration_seconds: float | None = None,
) -> dict[str, object]:
    total = len(results)
    success = sum(1 for result in results if result.success)
    elapsed_values = [result.elapsed_ms for result in results]
    measured_duration = max(duration_seconds or 0.0, 0.0)
    status_codes = Counter(str(result.status_code) for result in results if result.status_code is not None)
    return {
        "total": total,
        "success": success,
        "failed": total - success,
        "success_rate": success / total if total else 0.0,
        "avg_ms": sum(elapsed_values) / total if total else 0.0,
        "p50_ms": percentile(elapsed_values, 50),
        "p95_ms": percentile(elapsed_values, 95),
        "p99_ms": percentile(elapsed_values, 99),
        "min_ms": min(elapsed_values) if elapsed_values else 0.0,
        "max_ms": max(elapsed_values) if elapsed_values else 0.0,
        "duration_seconds": measured_duration,
        "throughput_rps": total / measured_duration if measured_duration else 0.0,
        "status_codes": dict(status_codes),
    }


# 将压测汇总结果格式化为命令行可读的中文报告。
def format_report(summary: dict[str, float | int]) -> str:
    return "\n".join(
        [
            f"请求数: {summary['total']}",
            f"成功: {summary['success']}",
            f"失败: {summary['failed']}",
            f"成功率: {summary['success_rate']:.0%}",
            f"平均耗时: {summary['avg_ms']:.0f}ms",
            f"P50耗时: {summary.get('p50_ms', 0.0):.0f}ms",
            f"P95耗时: {summary['p95_ms']:.0f}ms",
            f"P99耗时: {summary.get('p99_ms', 0.0):.0f}ms",
            f"最短耗时: {summary['min_ms']:.0f}ms",
            f"最长耗时: {summary['max_ms']:.0f}ms",
            f"吞吐量: {summary.get('throughput_rps', 0.0):.2f} requests/s",
        ]
    )


# 创建报告目录并以 UTF-8 写入性能测试 JSON 报告，不记录请求头密钥。
def write_json_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


# 发送一次问答请求并记录耗时，失败时保留错误信息。
async def run_one_request(
    client: httpx.AsyncClient,
    api_url: str,
    question: str,
    api_key: str = "",
) -> LoadTestResult:
    started_at = perf_counter()
    try:
        headers = {"X-API-Key": api_key.strip()} if api_key.strip() else None
        response = await client.post(api_url, json={"question": question}, headers=headers)
        elapsed_ms = (perf_counter() - started_at) * 1000
        return LoadTestResult(
            success=response.status_code == 200,
            elapsed_ms=elapsed_ms,
            status_code=response.status_code,
            error="" if response.status_code == 200 else response.text[:200],
        )
    except Exception as exc:
        elapsed_ms = (perf_counter() - started_at) * 1000
        return LoadTestResult(success=False, elapsed_ms=elapsed_ms, status_code=None, error=str(exc))


# 按指定并发数运行压测请求，使用信号量控制同时在途请求数。
async def run_load_test(
    api_url: str,
    question: str,
    request_count: int,
    concurrency: int,
    timeout_seconds: float,
    api_key: str = "",
) -> list[LoadTestResult]:
    semaphore = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)

    async with httpx.AsyncClient(timeout=timeout_seconds, limits=limits, trust_env=False) as client:

        # 包装单次请求，确保并发数不会超过用户指定值。
        async def run_limited_request() -> LoadTestResult:
            async with semaphore:
                return await run_one_request(client, api_url, question, api_key=api_key)

        return await asyncio.gather(*(run_limited_request() for _ in range(request_count)))


# 命令行入口：解析压测参数、运行请求并打印或保存汇总报告。
def main() -> None:
    parser = argparse.ArgumentParser(description="轻量压测 KF RAG 问答接口")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="问答接口地址")
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="压测使用的问题")
    parser.add_argument("-n", "--requests", type=int, default=10, help="总请求数")
    parser.add_argument("-c", "--concurrency", type=int, default=2, help="并发数")
    parser.add_argument("--timeout", type=float, default=120.0, help="单请求超时时间，单位秒")
    parser.add_argument("--api-key", default=os.getenv("APP_API_KEY", ""), help="可选的后端 API Key")
    parser.add_argument("--output", type=Path, help="可选的 JSON 报告输出路径")
    args = parser.parse_args()

    if args.requests <= 0:
        raise SystemExit("requests 必须大于 0")
    if args.concurrency <= 0:
        raise SystemExit("concurrency 必须大于 0")

    started_at = perf_counter()
    results = asyncio.run(
        run_load_test(
            api_url=args.url,
            question=args.question,
            request_count=args.requests,
            concurrency=args.concurrency,
            timeout_seconds=args.timeout,
            api_key=args.api_key,
        )
    )
    duration_seconds = perf_counter() - started_at
    summary = summarize_results(results, duration_seconds=duration_seconds)
    print(format_report(summary))
    if args.output:
        report = {
            "config": {
                "url": args.url,
                "question_length": len(args.question),
                "requests": args.requests,
                "concurrency": args.concurrency,
                "timeout_seconds": args.timeout,
            },
            "summary": summary,
        }
        write_json_report(args.output, report)
        print(f"JSON 报告已写入：{args.output}")


if __name__ == "__main__":
    main()
