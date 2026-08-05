import json
import sys
from pathlib import Path

import scripts.evaluate as evaluate_module
from app.evaluation.judge import JudgementCompletion, JudgementError
from app.schemas.chat import ChatResponse, SourceSnippet
from scripts.evaluate import eval_result_to_dict, evaluate_question, load_eval_questions, main, summarize_results


class NetworklessJudge:
    # 语义评测的假客户端：任何补全请求都抛错，确保 main 测试不触发真实 DeepSeek 调用。
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise JudgementError()


class FakeChain:
    # 模拟 RAG Chain，避免单元测试依赖真实向量库和大模型。
    def answer(self, question: str) -> ChatResponse:
        if "微信" in question:
            return ChatResponse(answer="手册中没有找到相关说明。", sources=[])
        return ChatResponse(
            answer=f"{question}：页面编辑器包括菜单栏和工具栏。",
            sources=[
                SourceSnippet(
                    title="页面编辑器/简介",
                    source_path="页面编辑器/简介.md",
                    snippet="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                    images=["页面编辑器/1.png"],
                    score=0.9,
                )
            ],
        )


class WorkflowChain:
    # 模拟流程类问题的合格回答，用来验证质量门禁规则。
    def answer(self, question: str) -> ChatResponse:
        return ChatResponse(
            answer="先新建工程，再发布，到运维中心部署并启动。",
            sources=[
                SourceSnippet(
                    title="教程/数据组态工程的启动",
                    source_path="教程/KingScada数据接入.html",
                    snippet="打开运维中心，添加端口，部署并启动。",
                    evidence_ids=["资料 1"],
                    images=["教程/1.png"],
                    score=0.9,
                )
            ],
        )


class ForbiddenSourceChain:
    # 模拟命中错误来源的回答，用来验证禁止来源门禁会拦截。
    def answer(self, question: str) -> ChatResponse:
        return ChatResponse(
            answer="打开运维中心部署并启动。",
            sources=[
                SourceSnippet(
                    title="数据APP组态/工程管理",
                    source_path="数据APP组态/工程管理/工程管理.html",
                    snippet="工程管理包括新建、编辑、删除。",
                    evidence_ids=["资料 1"],
                    images=[],
                    score=0.9,
                )
            ],
        )


def test_default_eval_file_points_to_evaluation_cases_directory():
    assert evaluate_module.DEFAULT_EVAL_FILE == Path("evaluation_cases/eval_questions.json")


def test_load_eval_questions_reads_json_file(tmp_path: Path):
    eval_file = tmp_path / "eval.json"
    eval_file.write_text(
        json.dumps(
            [
                {
                    "question": "页面编辑器主要包括哪些区域？",
                    "expected_keywords": ["菜单栏", "工具栏"],
                    "expected_source_keywords": ["页面编辑器/简介"],
                    "forbidden_source_keywords": ["无关来源"],
                    "expect_images": True,
                    "min_sources": 1,
                    "min_images": 1,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    questions = load_eval_questions(eval_file)

    assert questions[0].question == "页面编辑器主要包括哪些区域？"
    assert questions[0].expected_keywords == ["菜单栏", "工具栏"]
    assert questions[0].expected_source_keywords == ["页面编辑器/简介"]
    assert questions[0].forbidden_source_keywords == ["无关来源"]
    assert questions[0].expect_images is True
    assert questions[0].min_sources == 1
    assert questions[0].min_images == 1
    assert questions[0].expect_no_answer is False


def test_evaluate_question_checks_keywords_sources_and_images():
    result = evaluate_question(
        chain=FakeChain(),
        question="页面编辑器主要包括哪些区域？",
        expected_keywords=["菜单栏", "配置窗"],
        expected_source_keywords=["页面编辑器/简介"],
        expect_images=True,
        expect_no_answer=False,
    )

    assert result.passed is True
    assert result.matched_keywords == ["菜单栏", "配置窗"]
    assert result.missing_keywords == []
    assert result.matched_source_keywords == ["页面编辑器/简介"]
    assert result.missing_source_keywords == []
    assert result.image_count == 1
    assert result.sources[0] == "页面编辑器/简介.md"


def test_evaluate_question_checks_min_images_and_forbidden_sources():
    result = evaluate_question(
        chain=WorkflowChain(),
        question="如何启动数据组态工程？",
        expected_keywords=["运维中心", "部署", "启动"],
        expected_source_keywords=["教程"],
        expect_images=True,
        expect_no_answer=False,
        forbidden_source_keywords=["工程管理/工程管理"],
        min_sources=1,
        min_images=1,
    )

    assert result.passed is True


def test_evaluate_question_fails_when_forbidden_source_matches():
    result = evaluate_question(
        chain=ForbiddenSourceChain(),
        question="如何启动数据组态工程？",
        expected_keywords=["运维中心", "部署", "启动"],
        expected_source_keywords=[],
        expect_images=False,
        expect_no_answer=False,
        forbidden_source_keywords=["数据APP组态/工程管理/工程管理"],
    )

    assert result.passed is False
    assert result.forbidden_source_matches == ["数据APP组态/工程管理/工程管理"]


def test_evaluate_question_checks_expected_no_answer():
    result = evaluate_question(
        chain=FakeChain(),
        question="手册里有没有微信登录说明？",
        expected_keywords=["手册中没有找到相关说明"],
        expected_source_keywords=[],
        expect_images=False,
        expect_no_answer=True,
    )

    assert result.passed is True
    assert result.no_answer_matched is True
    assert result.sources == []


def test_summarize_results_calculates_pass_rate():
    results = [
        evaluate_question(FakeChain(), "问题一", ["菜单栏"], [], False, False),
        evaluate_question(FakeChain(), "问题二", ["不存在的词"], [], False, False),
    ]

    summary = summarize_results(results)

    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["pass_rate"] == 0.5


def test_summarize_results_includes_rule_level_pass_rates():
    results = [
        evaluate_question(FakeChain(), "问题一", ["菜单栏"], ["页面编辑器/简介"], True, False),
        evaluate_question(FakeChain(), "手册里有没有微信登录说明？", ["不存在的词"], [], False, True),
    ]

    summary = summarize_results(results)

    assert summary["keyword_pass_rate"] == 0.5
    assert summary["source_pass_rate"] == 1.0
    assert summary["image_pass_rate"] == 1.0
    assert summary["no_answer_pass_rate"] == 1.0


def test_eval_result_to_dict_returns_json_safe_result_fields():
    result = evaluate_question(
        FakeChain(),
        "页面编辑器主要包括哪些区域？",
        ["菜单栏"],
        ["页面编辑器/简介"],
        True,
        False,
    )

    payload = eval_result_to_dict(result)

    assert payload["question"] == "页面编辑器主要包括哪些区域？"
    assert payload["passed"] is True
    assert payload["answer"]
    assert payload["sources"] == ["页面编辑器/简介.md"]
    assert payload["missing_keywords"] == []
    assert payload["image_count"] == 1
    assert payload["source_count"] == 1


def test_evaluate_main_writes_json_report_and_returns_zero_for_passing_questions(tmp_path: Path, monkeypatch):
    eval_file = tmp_path / "eval.json"
    output_file = tmp_path / "reports" / "evaluation.json"
    eval_file.write_text(
        json.dumps([{"question": "问题", "expected_keywords": ["菜单栏"]}], ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(evaluate_module, "create_rag_chain", lambda: FakeChain())
    monkeypatch.setattr(evaluate_module, "create_judgement_client", lambda settings: NetworklessJudge())
    monkeypatch.setattr(
        sys,
        "argv",
        ["evaluate", "--file", str(eval_file), "--output", str(output_file)],
    )

    exit_code = main()

    assert exit_code == 0
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["summary"]["total"] == 1
    assert payload["results"][0]["question"] == "问题"


def test_evaluate_main_returns_one_for_failed_questions(tmp_path: Path, monkeypatch):
    eval_file = tmp_path / "eval.json"
    eval_file.write_text(
        json.dumps([{"question": "问题", "expected_keywords": ["不存在的词"]}], ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(evaluate_module, "create_rag_chain", lambda: FakeChain())
    monkeypatch.setattr(evaluate_module, "create_judgement_client", lambda settings: NetworklessJudge())
    monkeypatch.setattr(sys, "argv", ["evaluate", "--file", str(eval_file)])

    assert main() == 1


def test_evaluate_main_reports_missing_file_in_chinese(tmp_path: Path, monkeypatch, capsys):
    missing_file = tmp_path / "missing.json"
    monkeypatch.setattr(sys, "argv", ["evaluate", "--file", str(missing_file)])

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "评测文件" in captured.err


def test_evaluate_main_without_file_delegates_to_local_gate(monkeypatch, capsys):
    import scripts.evaluation_gate as gate_module

    monkeypatch.setattr(gate_module, "main", lambda argv: 1)

    assert main(["--suite", "core", "--mode", "blocking"]) == 1

    assert "deprecated" in capsys.readouterr().err


def test_evaluate_question_records_faithfulness(monkeypatch):
    from scripts.evaluate import EvalResult, evaluate_question
    from app.schemas.chat import ChatResponse, SourceSnippet

    class FakeChain:
        def answer(self, question):
            return ChatResponse(
                answer="按钮可配置颜色。",
                sources=[SourceSnippet(title="t", source_path="p.md", snippet="按钮可配置颜色。", evidence_ids=["资料 1"], images=[], score=0.9)],
            )

    class FakeJudge:
        def complete_json(self, system_prompt, user_prompt):
            if "拆" in system_prompt:
                return JudgementCompletion({"claims": [{"claim": "按钮可配置颜色。", "supported": True, "evidence": "按钮可配置颜色。"}]})
            return JudgementCompletion({"supported": True, "evidence": "按钮可配置颜色。"})

    result = evaluate_question(FakeChain(), "问题", [], [], False, False, judge=FakeJudge(), semantic_enabled=True)
    assert result.faithfulness_score == 1.0
    assert len(result.faithfulness_claims) == 1
