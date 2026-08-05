import sqlite3
from pathlib import Path

import pytest

from app.evaluation.gates import evaluate_gates
from app.evaluation.models import CaseResult, EvaluationRunSummary, TurnResult
from app.evaluation.repository import EvaluationRepository


# 构造一轮评测结果，覆盖 JSON 字段和来源字段的持久化。
def _turn_result() -> TurnResult:
    return TurnResult(
        question="如何创建采集工程？",
        answer="点击新建工程，填写名称。[资料 1]",
        standalone_question="如何创建采集工程？",
        passed=True,
        keyword_passed=True,
        source_passed=True,
        image_passed=True,
        no_answer_passed=True,
        matched_keywords=["新建工程", "名称"],
        matched_source_keywords=["数采管理"],
        sources=[{"title": "数采管理", "source_path": "html/数采管理/index.html"}],
        image_count=1,
        source_count=1,
        elapsed_ms=120,
    )


# 构造一个用例结果，作为存储层测试的稳定输入。
def _case_result(case_id: str = "single.collect.create") -> CaseResult:
    return CaseResult(
        case_id=case_id,
        category="数采管理",
        priority="P0",
        case_type="single",
        passed=True,
        turn_results=[_turn_result()],
        elapsed_ms=120,
    )


# 构造一次运行汇总，作为 evaluation_runs 表的稳定输入。
def _summary(run_id: str = "run-1") -> EvaluationRunSummary:
    return EvaluationRunSummary(
        run_id=run_id,
        status="completed",
        case_total=1,
        case_passed=1,
        pass_rate=1.0,
        p0_total=1,
        p0_passed=1,
        avg_latency_ms=120,
        p95_latency_ms=120,
        single_total=1,
        single_passed=1,
        category_pass_rates={"数采管理": 1.0},
    )


# 验证初始化会创建数据库文件和评测平台需要的表。
def test_repository_initialize_creates_database_tables(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "evaluation" / "eval.db")

    repository.initialize()

    assert repository.db_path.exists()
    assert set(repository.list_table_names()) >= {
        "evaluation_runs",
        "evaluation_case_results",
        "evaluation_turn_results",
    }


# 验证保存运行后，详情能读回汇总、用例结果和轮次结果。
def test_repository_saves_and_loads_run_detail(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    summary = _summary()
    case_results = [_case_result()]
    gate_result = evaluate_gates(summary, fail_under=0.8, max_p95_ms=30000)

    run_id = repository.save_run(summary, case_results, gate_result)
    detail = repository.get_run(run_id)

    assert detail is not None
    assert detail.summary.run_id == "run-1"
    assert detail.gate_result.passed is True
    assert detail.case_results[0].case_id == "single.collect.create"
    assert detail.case_results[0].turn_results[0].matched_keywords == ["新建工程", "名称"]
    assert detail.case_results[0].turn_results[0].sources[0]["title"] == "数采管理"


# 验证运行列表按最新开始时间倒序返回。
def test_repository_lists_runs_newest_first(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    repository.save_run(_summary("run-old"), [_case_result("case-old")], evaluate_gates(_summary("run-old"), 0.8, None))
    repository.save_run(_summary("run-new"), [_case_result("case-new")], evaluate_gates(_summary("run-new"), 0.8, None))

    runs = repository.list_runs(limit=10)

    assert [run.run_id for run in runs] == ["run-new", "run-old"]


# 验证从数据库读取运行列表时，会恢复单轮/多轮和分类通过率统计。
def test_repository_list_runs_restores_case_breakdowns(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    summary = EvaluationRunSummary(
        run_id="run-breakdown",
        status="completed",
        case_total=2,
        case_passed=1,
        pass_rate=0.5,
        p0_total=1,
        p0_passed=1,
        avg_latency_ms=120,
        p95_latency_ms=120,
        single_total=1,
        single_passed=1,
        dialogue_total=1,
        dialogue_passed=0,
        category_pass_rates={"数采管理": 1.0, "页面编辑器": 0.0},
    )
    case_results = [
        _case_result("single.collect.create"),
        CaseResult(
            case_id="dialog.editor.areas",
            category="页面编辑器",
            priority="P1",
            case_type="dialogue",
            passed=False,
            turn_results=[_turn_result()],
            failure_reasons=["第 1 轮缺少答案关键词：工具栏"],
            elapsed_ms=120,
        ),
    ]
    repository.save_run(summary, case_results, evaluate_gates(summary, 0.8, None))

    run = repository.list_runs(limit=1)[0]

    assert run.single_total == 1
    assert run.single_passed == 1
    assert run.dialogue_total == 1
    assert run.dialogue_passed == 0
    assert run.category_pass_rates == {"数采管理": 1.0, "页面编辑器": 0.0}


# 验证可以找到指定运行之前最近一次已完成运行，供历史对比使用。
def test_repository_get_previous_completed_run(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    repository.save_run(_summary("run-1"), [_case_result("case-1")], evaluate_gates(_summary("run-1"), 0.8, None))
    repository.save_run(_summary("run-2"), [_case_result("case-2")], evaluate_gates(_summary("run-2"), 0.8, None))

    previous = repository.get_previous_completed_run("run-2")

    assert previous is not None
    assert previous.summary.run_id == "run-1"


def test_repository_upgrades_old_database_and_preserves_existing_run(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    connection = sqlite3.connect(db_path)
    connection.executescript("""
        CREATE TABLE evaluation_runs (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL, case_total INTEGER NOT NULL, case_passed INTEGER NOT NULL,
            pass_rate REAL NOT NULL, p0_total INTEGER NOT NULL, p0_passed INTEGER NOT NULL,
            avg_latency_ms REAL NOT NULL, p95_latency_ms REAL NOT NULL, gate_passed INTEGER NOT NULL,
            gate_reasons_json TEXT NOT NULL, config_json TEXT NOT NULL, error TEXT
        );
        CREATE TABLE evaluation_turn_results (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, case_result_id TEXT NOT NULL);
        INSERT INTO evaluation_runs VALUES ('legacy', 'completed', 'start', 'finish', 1, 1, 1, 1, 1, 1, 1, 1, '[]', '{}', NULL);
    """)
    connection.close()

    repository = EvaluationRepository(db_path)
    repository.initialize()

    with repository._connect() as connection:
        tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert connection.execute("SELECT id FROM evaluation_runs WHERE id = 'legacy'").fetchone()["id"] == "legacy"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert {"evaluation_case_results", "evaluation_metric_results", "evaluation_baselines"} <= tables


def test_repository_rejects_empty_run_and_approved_baselines_are_immutable(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")

    with pytest.raises(ValueError, match="at least one case"):
        repository.create_run("core", "v1", "hash", {}, "CALIBRATION", case_total=0)

    run_id = repository.create_run("core", "v1", "hash", {}, "CALIBRATION", case_total=1)
    repository.approve_baseline(run_id, approved_by="tester")

    with pytest.raises(ValueError, match="immutable"):
        repository.approve_baseline(run_id, approved_by="other")
    assert repository.get_current_baseline("core") == run_id


def test_repository_persists_and_lists_approved_baseline_note(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    run_id = repository.create_run("core", "v1", "hash", {}, "CALIBRATION", case_total=1)

    repository.approve_baseline(run_id, approved_by="release manager", note="known-good release")

    baselines = repository.list_baselines()

    assert len(baselines) == 1
    assert baselines[0]["suite_id"] == "core"
    assert baselines[0]["run_id"] == run_id
    assert baselines[0]["approved_by"] == "release manager"
    assert baselines[0]["note"] == "known-good release"
    assert baselines[0]["approved_at"]


def test_repository_adds_note_to_existing_baselines_without_losing_approvals(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    connection = sqlite3.connect(db_path)
    connection.executescript("""
        CREATE TABLE evaluation_runs (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL, case_total INTEGER NOT NULL, case_passed INTEGER NOT NULL,
            pass_rate REAL NOT NULL, p0_total INTEGER NOT NULL, p0_passed INTEGER NOT NULL,
            avg_latency_ms REAL NOT NULL, p95_latency_ms REAL NOT NULL, gate_passed INTEGER NOT NULL,
            gate_reasons_json TEXT NOT NULL, config_json TEXT NOT NULL, error TEXT
        );
        CREATE TABLE evaluation_baselines (
            id TEXT PRIMARY KEY, suite_id TEXT NOT NULL, run_id TEXT NOT NULL UNIQUE,
            approved_at TEXT NOT NULL, approved_by TEXT
        );
        INSERT INTO evaluation_runs VALUES ('legacy', 'completed', 'start', 'finish', 1, 1, 1, 1, 1, 1, 1, 1, '[]', '{}', NULL);
        INSERT INTO evaluation_baselines VALUES ('baseline-legacy', 'core', 'legacy', 'approved', 'tester');
    """)
    connection.close()

    repository = EvaluationRepository(db_path)
    repository.initialize()

    with repository._connect() as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(evaluation_baselines)")}
    assert "note" in columns
    assert repository.list_baselines()[0] == {
        "suite_id": "core",
        "run_id": "legacy",
        "approved_at": "approved",
        "approved_by": "tester",
        "note": None,
    }


def test_repository_invalidates_orphaned_active_run_on_initialize(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    repository.initialize()
    with repository._connect() as connection:
        connection.execute(
            """
            INSERT INTO evaluation_runs (
                id, status, started_at, finished_at, case_total, case_passed, pass_rate,
                p0_total, p0_passed, avg_latency_ms, p95_latency_ms, gate_passed,
                gate_reasons_json, config_json
            ) VALUES ('orphaned', 'running', 'start', 'finish', 1, 0, 0, 0, 0, 0, 0, 0, '[]', '{}')
            """
        )

    repository.initialize()

    with repository._connect() as connection:
        row = connection.execute("SELECT status, error FROM evaluation_runs WHERE id = 'orphaned'").fetchone()
    assert (row["status"], row["error"]) == ("INVALID", "process_interrupted")


def test_repository_database_constraint_allows_only_one_active_status(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    run_id = repository.create_run("core", "v1", "hash", {}, "CALIBRATION", case_total=1)
    repository.transition_run(run_id, "running")

    with repository._connect() as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO evaluation_runs (
                id, status, started_at, finished_at, case_total, case_passed, pass_rate,
                p0_total, p0_passed, avg_latency_ms, p95_latency_ms, gate_passed,
                gate_reasons_json, config_json
            ) VALUES ('second-active', 'created', 'start', 'finish', 1, 0, 0, 0, 0, 0, 0, 0, '[]', '{}')
            """
        )


def test_repository_migrates_legacy_database_with_multiple_active_statuses(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    connection = sqlite3.connect(db_path)
    connection.executescript("""
        CREATE TABLE evaluation_runs (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL, case_total INTEGER NOT NULL, case_passed INTEGER NOT NULL,
            pass_rate REAL NOT NULL, p0_total INTEGER NOT NULL, p0_passed INTEGER NOT NULL,
            avg_latency_ms REAL NOT NULL, p95_latency_ms REAL NOT NULL, gate_passed INTEGER NOT NULL,
            gate_reasons_json TEXT NOT NULL, config_json TEXT NOT NULL, error TEXT
        );
        CREATE TABLE evaluation_turn_results (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, case_result_id TEXT NOT NULL);
        CREATE UNIQUE INDEX evaluation_runs_one_active ON evaluation_runs(status)
            WHERE lower(status) IN ('created', 'running', 'scoring');
    """)
    for status in ("created", "running", "scoring"):
        connection.execute(
            """
            INSERT INTO evaluation_runs VALUES (?, ?, 'start', 'finish', 1, 0, 0, 0, 0, 0, 0, 0, '[]', '{}', NULL)
            """,
            (status, status),
        )
    connection.commit()
    connection.close()

    repository = EvaluationRepository(db_path)
    repository.initialize()

    with repository._connect() as connection:
        rows = connection.execute("SELECT status, error FROM evaluation_runs ORDER BY id").fetchall()
    assert [(row["status"], row["error"]) for row in rows] == [
        ("created", None),
        ("INVALID", "process_interrupted"),
        ("INVALID", "process_interrupted"),
    ]
