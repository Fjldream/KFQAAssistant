import json
from pathlib import Path

from app.evaluation.repository import EvaluationRepository
from app.evaluation.models import CaseResult, TurnResult
from app.evaluation.service import EvaluationService
from app.schemas.chat import ChatResponse, SourceSnippet


class FakeChain:
    # 评测服务测试使用假 Chain，避免单元测试调用真实模型。
    def answer(self, question: str, conversation_summary="", conversation_turn_count=0, recent_messages=None):
        return ChatResponse(
            answer="点击新建工程，填写名称。[资料 1]",
            sources=[
                SourceSnippet(
                    title="数采管理/工程开发-Windows",
                    source_path="html/数采管理/工程开发-Windows/index.html",
                    snippet="新建工程并填写名称。",
                )
            ],
            standalone_question=question,
        )


# 写入最小评测集，方便服务层测试聚焦业务编排。
def _write_cases(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "id": "single.collect.create",
                    "category": "数采管理",
                    "priority": "P0",
                    "question": "如何创建采集工程？",
                    "expected_keywords": ["新建工程", "名称"],
                    "expected_source_keywords": ["数采管理"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# 验证服务可以读取评测用例，并统一返回单轮/多轮结构。
def test_service_lists_cases(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
    )

    cases = service.list_cases()

    assert cases[0].id == "single.collect.create"
    assert cases[0].case_type == "single"


# 验证服务可以执行评测、保存运行，并返回可查询详情。
def test_service_runs_evaluation_and_saves_detail(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
    )

    detail = service.run_evaluation(include_dialogues=False)
    loaded = service.get_run(detail.summary.run_id)

    assert detail.summary.case_total == 1
    assert detail.gate_result.passed is True
    assert loaded is not None
    assert loaded.case_results[0].case_id == "single.collect.create"


# 验证服务可以只运行一条用例，支持前端逐条展示进度。
def test_service_runs_single_case_by_id(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
    )

    result = service.run_case("single.collect.create", include_dialogues=False)

    assert result is not None
    assert result.case_id == "single.collect.create"
    assert result.passed is True


# 验证服务可以保存前端逐条评测得到的结果，形成一次完整运行报告。
def test_service_saves_case_results_as_run(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
    )
    case_result = CaseResult(
        case_id="single.collect.create",
        category="数采管理",
        priority="P0",
        case_type="single",
        passed=True,
        turn_results=[
            TurnResult(
                question="如何创建采集工程？",
                answer="点击新建工程。",
                standalone_question="如何创建采集工程？",
                passed=True,
                keyword_passed=True,
                source_passed=True,
                image_passed=True,
                no_answer_passed=True,
            )
        ],
    )

    detail = service.save_case_results([case_result], config={"mode": "progressive"})

    assert detail.summary.case_total == 1
    assert detail.gate_result.passed is True
    assert service.get_run(detail.summary.run_id) is not None


# 验证服务总览会返回最近一次运行和上一轮对比结果。
def test_service_returns_overview_with_latest_run_and_comparison(tmp_path: Path):
    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
    )
    first = service.run_evaluation(include_dialogues=False)
    second = service.run_evaluation(include_dialogues=False)

    overview = service.get_overview()

    assert overview.latest.summary.run_id == second.summary.run_id
    assert overview.comparison is not None
    assert overview.comparison.pass_rate_delta == 0
    assert overview.previous_run_id == first.summary.run_id


# 验证 semantic_enabled=True 时 run_case 会启用 judge 计算 faithfulness，
# 修复前端评测中心 progressive 路径从未产生忠实度值的问题。
def test_service_run_case_computes_faithfulness_when_semantic_enabled(tmp_path, monkeypatch):
    import app.evaluation.service as service_module
    from app.evaluation.judge import JudgementError

    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
        semantic_enabled=True,
    )

    class FakeJudge:
        def complete_json(self, system_prompt, user_prompt):
            if "拆" in system_prompt:
                return {"claims": ["点击新建工程填写名称"]}
            return {"supported": True, "evidence": "新建工程并填写名称。"}

    monkeypatch.setattr(service_module, "create_judgement_client", lambda settings: FakeJudge())

    result = service.run_case("single.collect.create", include_dialogues=False)

    assert result is not None
    turn = result.turn_results[0]
    assert turn.faithfulness_score is not None
    assert len(turn.faithfulness_claims) == 1


# 验证默认（semantic_enabled=False）时 run_case 不产生 faithfulness，保持既有行为。
def test_service_run_case_skips_judge_by_default(tmp_path, monkeypatch):
    import app.evaluation.service as service_module

    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
    )

    def boom(*args, **kwargs):
        raise AssertionError("semantic_enabled=False 时不应构造 judge")

    monkeypatch.setattr(service_module, "create_judgement_client", boom)

    result = service.run_case("single.collect.create", include_dialogues=False)

    assert result is not None
    assert result.turn_results[0].faithfulness_score is None
