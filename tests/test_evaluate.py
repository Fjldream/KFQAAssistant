import json
from pathlib import Path

from app.schemas.chat import ChatResponse, SourceSnippet
from scripts.evaluate import evaluate_question, load_eval_questions, summarize_results


class FakeChain:
    # 模拟 RAG Chain，避免单元测试依赖真实向量库和大模型。
    def answer(self, question: str) -> ChatResponse:
        return ChatResponse(
            answer=f"{question}：页面编辑器包括菜单栏和工具栏。",
            sources=[
                SourceSnippet(
                    title="页面编辑器/简介",
                    source_path="页面编辑器/简介.md",
                    snippet="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                    images=[],
                    score=0.9,
                )
            ],
        )


def test_load_eval_questions_reads_json_file(tmp_path: Path):
    eval_file = tmp_path / "eval.json"
    eval_file.write_text(
        json.dumps(
            [
                {
                    "question": "页面编辑器主要包括哪些区域？",
                    "expected_keywords": ["菜单栏", "工具栏"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    questions = load_eval_questions(eval_file)

    assert questions[0].question == "页面编辑器主要包括哪些区域？"
    assert questions[0].expected_keywords == ["菜单栏", "工具栏"]


def test_evaluate_question_checks_keywords_in_answer_and_sources():
    result = evaluate_question(
        chain=FakeChain(),
        question="页面编辑器主要包括哪些区域？",
        expected_keywords=["菜单栏", "配置窗"],
    )

    assert result.passed is True
    assert result.matched_keywords == ["菜单栏", "配置窗"]
    assert result.missing_keywords == []
    assert result.sources[0] == "页面编辑器/简介.md"


def test_summarize_results_calculates_pass_rate():
    results = [
        evaluate_question(FakeChain(), "问题一", ["菜单栏"]),
        evaluate_question(FakeChain(), "问题二", ["不存在的词"]),
    ]

    summary = summarize_results(results)

    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["pass_rate"] == 0.5
