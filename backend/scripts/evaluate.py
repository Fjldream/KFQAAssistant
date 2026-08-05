import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence

from app.core.config import get_settings
from app.evaluation.judge import create_judgement_client
from app.evaluation.metrics_registry import get_metric
from app.rag.generation.answer_policy import is_no_answer
from app.rag.factory import create_rag_chain
from app.schemas.chat import ChatResponse

DEFAULT_EVAL_FILE = Path("evaluation_cases/eval_questions.json")


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
    forbidden_source_keywords: list[str] = field(default_factory=list)
    min_sources: int = 0
    min_images: int = 0


@dataclass(frozen=True)
class EvalResult:
    question: str
    passed: bool
    matched_keywords: list[str]
    missing_keywords: list[str]
    matched_source_keywords: list[str]
    missing_source_keywords: list[str]
    forbidden_source_matches: list[str]
    image_count: int
    source_count: int
    no_answer_matched: bool
    sources: list[str]
    answer: str
    keyword_passed: bool
    source_passed: bool
    image_passed: bool
    no_answer_passed: bool
    faithfulness_score: float | None = None
    faithfulness_claims: list[dict] = field(default_factory=list)


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
            forbidden_source_keywords=[str(keyword) for keyword in item.get("forbidden_source_keywords", [])],
            min_sources=int(item.get("min_sources", 0)),
            min_images=int(item.get("min_images", 0)),
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


# 判断图片数量是否达到显式门槛，兼容旧的 expect_images 布尔规则。
def _image_requirement_matched(image_count: int, expect_images: bool, min_images: int) -> bool:
    required_images = max(1 if expect_images else 0, min_images)
    return image_count >= required_images


# 统计结果列表中某条质量规则的通过率，空列表返回 0，避免除零异常。
def _pass_rate(results: list[EvalResult], attribute: str) -> float:
    if not results:
        return 0.0
    passed = sum(1 for result in results if getattr(result, attribute))
    return passed / len(results)


# 评估单个问题：检查关键词、来源、图片和拒答行为是否符合预期。
def evaluate_question(
    chain: ChainProtocol,
    question: str,
    expected_keywords: list[str],
    expected_source_keywords: list[str],
    expect_images: bool,
    expect_no_answer: bool,
    forbidden_source_keywords: list[str] | None = None,
    min_sources: int = 0,
    min_images: int = 0,
    judge=None,
    semantic_enabled: bool = True,
) -> EvalResult:
    forbidden_source_keywords = forbidden_source_keywords or []
    response = chain.answer(question)
    searchable_text = _searchable_text(response)
    source_text = _source_text(response)
    image_count = _image_count(response)
    source_count = len(response.sources)
    actual_no_answer = is_no_answer(response.answer)
    matched_keywords = [keyword for keyword in expected_keywords if keyword in searchable_text]
    missing_keywords = [keyword for keyword in expected_keywords if keyword not in searchable_text]
    matched_source_keywords = [keyword for keyword in expected_source_keywords if keyword in source_text]
    missing_source_keywords = [keyword for keyword in expected_source_keywords if keyword not in source_text]
    forbidden_source_matches = [keyword for keyword in forbidden_source_keywords if keyword in source_text]
    image_matched = _image_requirement_matched(image_count, expect_images, min_images)
    source_count_matched = source_count >= min_sources
    no_answer_matched = actual_no_answer is expect_no_answer
    keyword_passed = not missing_keywords
    source_passed = not missing_source_keywords and not forbidden_source_matches and source_count_matched
    no_answer_passed = no_answer_matched
    passed = (
        keyword_passed
        and source_passed
        and image_matched
        and no_answer_passed
    )
    faithfulness_score = None
    faithfulness_claims: list[dict] = []
    if semantic_enabled and judge is not None and not is_no_answer(response.answer) and response.sources:
        result = get_metric("faithfulness").evaluate(response.answer, [s.snippet for s in response.sources], judge)
        faithfulness_score = result.score
        faithfulness_claims = result.details.get("claims", [])
    return EvalResult(
        question=question,
        passed=passed,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        matched_source_keywords=matched_source_keywords,
        missing_source_keywords=missing_source_keywords,
        forbidden_source_matches=forbidden_source_matches,
        image_count=image_count,
        source_count=source_count,
        no_answer_matched=no_answer_matched,
        sources=[source.source_path for source in response.sources],
        answer=response.answer,
        keyword_passed=keyword_passed,
        source_passed=source_passed,
        image_passed=image_matched,
        no_answer_passed=no_answer_passed,
        faithfulness_score=faithfulness_score,
        faithfulness_claims=faithfulness_claims,
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
        "keyword_pass_rate": _pass_rate(results, "keyword_passed"),
        "source_pass_rate": _pass_rate(results, "source_passed"),
        "image_pass_rate": _pass_rate(results, "image_passed"),
        "no_answer_pass_rate": _pass_rate(results, "no_answer_passed"),
    }


# 将单题评测结果转换成不包含敏感信息的 JSON 对象，供报告保存和后续分析使用。
def eval_result_to_dict(result: EvalResult) -> dict[str, object]:
    return {
        "question": result.question,
        "passed": result.passed,
        "matched_keywords": result.matched_keywords,
        "missing_keywords": result.missing_keywords,
        "matched_source_keywords": result.matched_source_keywords,
        "missing_source_keywords": result.missing_source_keywords,
        "forbidden_source_matches": result.forbidden_source_matches,
        "image_count": result.image_count,
        "source_count": result.source_count,
        "no_answer_matched": result.no_answer_matched,
        "keyword_passed": result.keyword_passed,
        "source_passed": result.source_passed,
        "image_passed": result.image_passed,
        "no_answer_passed": result.no_answer_passed,
        "sources": result.sources,
        "answer": result.answer,
        "faithfulness_score": result.faithfulness_score,
        "faithfulness_claims": result.faithfulness_claims,
    }


# 构建包含汇总和逐题详情的结构化评测报告，方便保存和后续比较基线。
def build_evaluation_report(results: list[EvalResult]) -> dict[str, object]:
    return {
        "summary": summarize_results(results),
        "results": [eval_result_to_dict(result) for result in results],
    }


# 创建报告目录并以 UTF-8 写入格式化 JSON，确保中文内容可直接阅读。
def write_json_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


# 将评估结果打印成适合命令行阅读的中文报告。
def print_report(results: list[EvalResult]) -> None:
    summary = summarize_results(results)
    print(f"评估问题数: {summary['total']}")
    print(f"通过: {summary['passed']}")
    print(f"失败: {summary['failed']}")
    print(f"通过率: {summary['pass_rate']:.0%}")
    print(f"关键词规则通过率: {summary['keyword_pass_rate']:.0%}")
    print(f"来源规则通过率: {summary['source_pass_rate']:.0%}")
    print(f"图片规则通过率: {summary['image_pass_rate']:.0%}")
    print(f"拒答规则通过率: {summary['no_answer_pass_rate']:.0%}")
    print()

    for index, result in enumerate(results, start=1):
        status = "通过" if result.passed else "失败"
        print(f"{index}. [{status}] {result.question}")
        print(f"   命中关键词: {', '.join(result.matched_keywords) or '无'}")
        print(f"   缺失关键词: {', '.join(result.missing_keywords) or '无'}")
        print(f"   命中来源关键词: {', '.join(result.matched_source_keywords) or '无'}")
        print(f"   缺失来源关键词: {', '.join(result.missing_source_keywords) or '无'}")
        print(f"   禁止来源命中: {', '.join(result.forbidden_source_matches) or '无'}")
        print(f"   拒答匹配: {'是' if result.no_answer_matched else '否'}")
        print(f"   图片数量: {result.image_count}")
        print(f"   来源数量: {result.source_count}")
        print(f"   来源: {', '.join(result.sources) or '无'}")
        print(f"   忠实度: {result.faithfulness_score if result.faithfulness_score is not None else '未评估'}")
        for claim in result.faithfulness_claims:
            if not claim["supported"]:
                print(f"    幻觉句: {claim['claim']}")
        print()


# 命令行评估入口：批量运行评估集并用退出码标识质量门禁结果。
def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--file" not in argv and not any(argument.startswith("--file=") for argument in argv):
        print("scripts.evaluate is deprecated without --file; delegating to scripts.evaluation_gate.", file=sys.stderr)
        from scripts.evaluation_gate import main as evaluation_gate_main

        return evaluation_gate_main(argv)

    parser = argparse.ArgumentParser(description="评估 KF RAG 问答效果")
    parser.add_argument("--file", type=Path, required=True, help="评估问题 JSON 文件")
    parser.add_argument("--output", type=Path, help="可选的 JSON 报告输出路径")
    args = parser.parse_args(argv)

    try:
        questions = load_eval_questions(args.file)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"评测文件处理失败：{exc}", file=sys.stderr)
        return 2

    chain = create_rag_chain()
    settings = get_settings()
    judge = create_judgement_client(settings)
    results = [
        evaluate_question(
            chain=chain,
            question=item.question,
            expected_keywords=item.expected_keywords,
            expected_source_keywords=item.expected_source_keywords,
            expect_images=item.expect_images,
            expect_no_answer=item.expect_no_answer,
            forbidden_source_keywords=item.forbidden_source_keywords,
            min_sources=item.min_sources,
            min_images=item.min_images,
            judge=judge,
            semantic_enabled=settings.evaluation_semantic_enabled,
        )
        for item in questions
    ]
    print_report(results)
    if args.output:
        write_json_report(args.output, build_evaluation_report(results))
        print(f"JSON 报告已写入：{args.output}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
