import json
from pathlib import Path

import pytest

from app.evaluation.repository import EvaluationRepository
from app.evaluation.models import GateMode
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
        evaluation_metrics="hit_at_k",
    )

    cases = service.list_cases()

    assert cases[0].id == "single.collect.create"
    assert cases[0].case_type == "single"


def test_service_validates_ordered_configured_metrics_before_run(tmp_path: Path):
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
        evaluation_metrics="faithfulness, answer_correctness, hit_at_k",
    )

    assert service.metrics == ("faithfulness", "answer_correctness", "hit_at_k")


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
        evaluation_metrics="hit_at_k",
    )

    detail = service.run_evaluation(include_dialogues=False)
    loaded = service.get_run(detail.summary.run_id)

    assert detail.summary.case_total == 1
    assert detail.gate_result.passed is True
    assert loaded is not None
    assert loaded.case_results[0].case_id == "single.collect.create"


def test_service_create_run_uses_trusted_coordinator_not_client_case_results(tmp_path: Path):
    class Coordinator:
        def __init__(self):
            self.calls = []

        def start(self, suite_id, mode):
            self.calls.append((suite_id, mode))
            return "trusted-run"

        def cancel(self, run_id):
            return run_id == "trusted-run"

    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    _write_cases(cases_path)
    coordinator = Coordinator()
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
        evaluation_metrics="hit_at_k",
        coordinator=coordinator,
    )

    assert service.create_run("legacy", GateMode.CALIBRATION) == "trusted-run"
    assert coordinator.calls == [("legacy", GateMode.CALIBRATION)]
    assert service.cancel_run("trusted-run") is True


def test_service_rejects_baseline_with_different_suite_version_or_hash(tmp_path: Path):
    service = EvaluationService.__new__(EvaluationService)
    repository = EvaluationRepository(tmp_path / "eval.db")
    baseline = repository.create_run("core", "1.0.0", "baseline-hash", {}, "CALIBRATION", case_total=1)
    with repository._connect() as connection:
        connection.execute("UPDATE evaluation_runs SET status = 'completed' WHERE id = ?", (baseline,))
    current = repository.create_run("core", "2.0.0", "current-hash", {}, "BLOCKING", case_total=1)
    service.repository = repository

    with pytest.raises(ValueError, match="suite_mismatch"):
        service.compare_to_baseline(current, baseline)


def test_trusted_service_default_metrics_complete_a_valid_run(tmp_path: Path, monkeypatch):
    import app.evaluation.service as service_module

    class Judge:
        def complete_json(self, system_prompt, user_prompt):
            if "correctness" in system_prompt:
                return {
                    "correctness": 1.0,
                    "relevance": 1.0,
                    "facts": [{"id": "fact-1", "covered": True}],
                    "forbidden_fact_matches": [],
                }
            return {"claims": [{"claim": "点击新建工程", "supported": True, "evidence": "资料"}]}

    cases_path = tmp_path / "cases.json"
    dialogues_path = tmp_path / "dialogues.json"
    cases_path.write_text(
        json.dumps(
            {
                "id": "trusted-core",
                "version": "v1",
                "default_thresholds": {
                    "answer_correctness": 0.8,
                    "faithfulness": 0.8,
                    "p1_required_fact_coverage": 0.8,
                },
                "cases": [{
                    "id": "single.collect.create",
                    "category": "数采管理",
                    "priority": "P1",
                    "question": "如何创建采集工程？",
                    "required_facts": [{"id": "fact-1", "text": "点击新建工程"}],
                }],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(service_module, "create_judgement_client", lambda settings: Judge())
    service = EvaluationService(
        repository=EvaluationRepository(tmp_path / "eval.db"),
        chain_factory=FakeChain,
        cases_path=cases_path,
        dialogues_path=dialogues_path,
        fail_under=0.8,
        max_p95_ms=30000,
        semantic_enabled=True,
    )
    try:
        assert {"hit_at_k", "recall_at_k", "mrr", "chunk_hit_at_k", "forbidden_source_matches"} <= set(service.metrics)
        run_id = service.create_run("trusted-core", GateMode.CALIBRATION)
        assert service.coordinator.wait_for_idle(timeout=2)

        detail = service.get_run(run_id)

        assert detail is not None
        assert detail.summary.status == "completed"
        assert detail.summary.missing_judge_metrics == []
    finally:
        service.shutdown()


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
        evaluation_metrics="hit_at_k",
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
        evaluation_metrics="hit_at_k",
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
            return {"claims": [{"claim": "点击新建工程填写名称", "supported": True, "evidence": "新建工程并填写名称。"}]}

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
    assert result.turn_results[0].metric_results[0].error_code == "judge_unavailable"
