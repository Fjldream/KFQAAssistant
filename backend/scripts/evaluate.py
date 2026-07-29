import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.rag.answer_policy import is_no_answer
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
    expected_source_keywords: list[str]
    expect_images: bool = False
    expect_no_answer: bool = False


@dataclass(frozen=True)
class EvalResult:
    question: str
    passed: bool
    matched_keywords: list[str]
    missing_keywords: list[str]
    matched_source_keywords: list[str]
    missing_source_keywords: list[str]
    image_count: int
    no_answer_matched: bool
    sources: list[str]
    answer: str


# 从 JSON 文件读取评估问题，每个问题可包含关键词、来源、图片和拒答预期。
def load_eval_questions(path: Path) -> list[EvalQuestion]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvalQuestion(
            question=str(item["question"]),
            expected_keywords=[str(keyword) for keyword in item.get("expected_keywords", [])],
            expected_source_keywords=[str(keyword) for keyword in item.get("expected_source_keywords", [])],
            expect_images=bool(item.get("expect_images", False)),
            expect_no_answer=bool(item.get("expect_no_answer", False)),
        )
        for item in raw_items
    ]


# 把回答正文和来源片段合并为一段文本，用来检查预期关键词是否被命中。
def _searchable_text(response: ChatResponse) -> str:
    snippets = [source.snippet for source in response.sources]
    return "\n".join([response.answer, *snippets])


# 合并来源路径和标题，用来判断检索是否命中了预期文档。
def _source_text(response: ChatResponse) -> str:
    return "\n".join(f"{source.title}\n{source.source_path}" for source in response.sources)


# 统计回答中返回的图片数量，用于检查应该带图的问题是否真的带图。
def _image_count(response: ChatResponse) -> int:
    return sum(len(source.images) for source in response.sources)


# 评估单个问题：检查关键词、来源、图片和拒答行为是否符合预期。
def evaluate_question(
    chain: ChainProtocol,
    question: str,
    expected_keywords: list[str],
    expected_source_keywords: list[str],
    expect_images: bool,
    expect_no_answer: bool,
) -> EvalResult:
    response = chain.answer(question)
    searchable_text = _searchable_text(response)
    source_text = _source_text(response)
    image_count = _image_count(response)
    actual_no_answer = is_no_answer(response.answer)
    matched_keywords = [keyword for keyword in expected_keywords if keyword in searchable_text]
    missing_keywords = [keyword for keyword in expected_keywords if keyword not in searchable_text]
    matched_source_keywords = [keyword for keyword in expected_source_keywords if keyword in source_text]
    missing_source_keywords = [keyword for keyword in expected_source_keywords if keyword not in source_text]
    image_matched = image_count > 0 if expect_images else True
    no_answer_matched = actual_no_answer is expect_no_answer
    passed = not missing_keywords and not missing_source_keywords and image_matched and no_answer_matched
    return EvalResult(
        question=question,
        passed=passed,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        matched_source_keywords=matched_source_keywords,
        missing_source_keywords=missing_source_keywords,
        image_count=image_count,
        no_answer_matched=no_answer_matched,
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
        print(f"   命中来源关键词: {', '.join(result.matched_source_keywords) or '无'}")
        print(f"   缺失来源关键词: {', '.join(result.missing_source_keywords) or '无'}")
        print(f"   拒答匹配: {'是' if result.no_answer_matched else '否'}")
        print(f"   图片数量: {result.image_count}")
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
            expected_source_keywords=item.expected_source_keywords,
            expect_images=item.expect_images,
            expect_no_answer=item.expect_no_answer,
        )
        for item in questions
    ]
    print_report(results)


if __name__ == "__main__":
    main()
