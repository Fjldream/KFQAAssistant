import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.rag.factory import create_rag_chain
from app.schemas.chat import ChatResponse


class ChainProtocol(Protocol):
    # 根据问题返回 RAG 问答结果，测试时可替换成假 Chain。
    def answer(self, question: str) -> ChatResponse:
        ...


@dataclass(frozen=True)
class EvalQuestion:
    question: str
    expected_keywords: list[str]


@dataclass(frozen=True)
class EvalResult:
    question: str
    passed: bool
    matched_keywords: list[str]
    missing_keywords: list[str]
    sources: list[str]
    answer: str


# 从 JSON 文件读取评估问题，每个问题包含 question 和 expected_keywords。
def load_eval_questions(path: Path) -> list[EvalQuestion]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvalQuestion(
            question=str(item["question"]),
            expected_keywords=[str(keyword) for keyword in item.get("expected_keywords", [])],
        )
        for item in raw_items
    ]


# 把回答正文和来源片段合并为一段文本，用来检查预期关键词是否被命中。
def _searchable_text(response: ChatResponse) -> str:
    snippets = [source.snippet for source in response.sources]
    return "\n".join([response.answer, *snippets])


# 评估单个问题：调用 RAG Chain，并检查答案或来源片段中是否包含预期关键词。
def evaluate_question(chain: ChainProtocol, question: str, expected_keywords: list[str]) -> EvalResult:
    response = chain.answer(question)
    searchable_text = _searchable_text(response)
    matched_keywords = [keyword for keyword in expected_keywords if keyword in searchable_text]
    missing_keywords = [keyword for keyword in expected_keywords if keyword not in searchable_text]
    return EvalResult(
        question=question,
        passed=not missing_keywords,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        sources=[source.source_path for source in response.sources],
        answer=response.answer,
    )


# 汇总评估结果，计算总题数、通过题数和通过率。
def summarize_results(results: list[EvalResult]) -> dict[str, float | int]:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total if total else 0.0,
    }


# 将评估结果打印成适合命令行阅读的中文报告。
def print_report(results: list[EvalResult]) -> None:
    summary = summarize_results(results)
    print(f"评估问题数: {summary['total']}")
    print(f"通过: {summary['passed']}")
    print(f"失败: {summary['failed']}")
    print(f"通过率: {summary['pass_rate']:.0%}")
    print()

    for index, result in enumerate(results, start=1):
        status = "通过" if result.passed else "失败"
        print(f"{index}. [{status}] {result.question}")
        print(f"   命中关键词: {', '.join(result.matched_keywords) or '无'}")
        print(f"   缺失关键词: {', '.join(result.missing_keywords) or '无'}")
        print(f"   来源数量: {len(result.sources)}")
        print(f"   来源: {', '.join(result.sources) or '无'}")
        print()


# 命令行评估入口：批量运行评估集，帮助判断 RAG 检索和回答质量。
def main() -> None:
    parser = argparse.ArgumentParser(description="评估 KF RAG 问答效果")
    parser.add_argument("--file", type=Path, default=Path("tests/eval_questions.json"), help="评估问题 JSON 文件")
    args = parser.parse_args()

    questions = load_eval_questions(args.file)
    chain = create_rag_chain()
    results = [
        evaluate_question(
            chain=chain,
            question=item.question,
            expected_keywords=item.expected_keywords,
        )
        for item in questions
    ]
    print_report(results)


if __name__ == "__main__":
    main()
