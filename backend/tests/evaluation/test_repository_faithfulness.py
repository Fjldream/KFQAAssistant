import json
from dataclasses import replace
from pathlib import Path

from app.evaluation.models import (
    CaseResult,
    EvaluationRunSummary,
    GateResult,
    MetricResult,
    MetricStatus,
    TurnResult,
)
from app.evaluation.repository import EvaluationRepository


def _turn() -> TurnResult:
    return TurnResult(
        question="q", answer="a", standalone_question=None, passed=True,
        keyword_passed=True, source_passed=True, image_passed=True, no_answer_passed=True,
        faithfulness_score=0.5,
        faithfulness_claims=[{"claim": "句1", "supported": False, "evidence": ""}],
        faithfulness_elapsed_ms=123.0,
    )


def test_repository_roundtrips_faithfulness(tmp_path: Path):
    repo = EvaluationRepository(tmp_path / "eval.db")
    summary = EvaluationRunSummary(run_id="r1", status="completed", case_total=1, case_passed=1, pass_rate=1.0,
                                   avg_faithfulness_score=0.5, knowledge_base_id="kb-1")
    case = CaseResult(case_id="c1", category="cat", priority="P1", case_type="single", passed=True,
                      turn_results=[_turn()])
    repo.save_run(summary, [case], GateResult(passed=True, reasons=[]))
    detail = repo.get_run("r1")
    assert detail is not None
    assert detail.summary.avg_faithfulness_score == 0.5
    assert detail.summary.knowledge_base_id == "kb-1"
    turn = detail.case_results[0].turn_results[0]
    assert turn.faithfulness_score == 0.5
    assert turn.faithfulness_claims == [{"claim": "句1", "supported": False, "evidence": ""}]
    assert turn.faithfulness_elapsed_ms == 123.0


def test_repository_migrates_old_schema(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    # 先建旧结构库（无新列）
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE evaluation_runs (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL, case_total INTEGER NOT NULL, case_passed INTEGER NOT NULL,
            pass_rate REAL NOT NULL, p0_total INTEGER NOT NULL, p0_passed INTEGER NOT NULL,
            avg_latency_ms REAL NOT NULL, p95_latency_ms REAL NOT NULL, gate_passed INTEGER NOT NULL,
            gate_reasons_json TEXT NOT NULL, config_json TEXT NOT NULL, error TEXT
        );
        CREATE TABLE evaluation_turn_results (
            id TEXT PRIMARY KEY, run_id TEXT NOT NULL, case_result_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL,
            standalone_question TEXT, passed INTEGER NOT NULL, keyword_passed INTEGER NOT NULL,
            source_passed INTEGER NOT NULL, image_passed INTEGER NOT NULL, no_answer_passed INTEGER NOT NULL,
            matched_keywords_json TEXT NOT NULL, missing_keywords_json TEXT NOT NULL,
            matched_source_keywords_json TEXT NOT NULL, missing_source_keywords_json TEXT NOT NULL,
            forbidden_source_matches_json TEXT NOT NULL, sources_json TEXT NOT NULL,
            image_count INTEGER NOT NULL, source_count INTEGER NOT NULL, elapsed_ms REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    # 插入一条旧格式行
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO evaluation_turn_results (
            id, run_id, case_result_id, turn_index, question, answer, standalone_question,
            passed, keyword_passed, source_passed, image_passed, no_answer_passed,
            matched_keywords_json, missing_keywords_json, matched_source_keywords_json,
            missing_source_keywords_json, forbidden_source_matches_json, sources_json,
            image_count, source_count, elapsed_ms
        ) VALUES ('t1', 'r1', 'cr1', 1, 'q', 'a', NULL, 1, 1, 1, 1, 1, '[]', '[]', '[]', '[]', '[]', '[]', 0, 0, 1.0)
    """)
    conn.commit()
    conn.close()
    # 初始化应自动补列，且旧行读取不报错
    repo = EvaluationRepository(db_path)
    repo.initialize()
    conn = sqlite3.connect(db_path)
    turn_cols = [row[1] for row in conn.execute("PRAGMA table_info(evaluation_turn_results)")]
    assert "faithfulness_score" in turn_cols
    assert "faithfulness_claims_json" in turn_cols
    assert "faithfulness_elapsed_ms" in turn_cols
    run_cols = [row[1] for row in conn.execute("PRAGMA table_info(evaluation_runs)")]
    assert "avg_faithfulness_score" in run_cols
    assert "knowledge_base_id" in run_cols
    conn.close()


def test_repository_checkpoints_case_and_generic_metrics_together(tmp_path: Path):
    repository = EvaluationRepository(tmp_path / "eval.db")
    run_id = repository.create_run("core", "v1", "hash", {}, "CALIBRATION", case_total=1)
    repository.transition_run(run_id, "running")
    metrics = [MetricResult(name="answer_correctness", score=0.9, status=MetricStatus.PASSED, threshold=0.8, details={"judge": "ok"})]
    case = CaseResult(
        case_id="c1", category="cat", priority="P1", case_type="single", passed=True,
        turn_results=[replace(_turn(), metric_results=metrics)],
    )

    repository.save_case_result(run_id, case)

    with repository._connect() as connection:
        row = connection.execute("SELECT metric_name, score, details_json FROM evaluation_metric_results WHERE run_id = ?", (run_id,)).fetchone()
    assert (row["metric_name"], row["score"], row["details_json"]) == ("answer_correctness", 0.9, '{"judge": "ok"}')
    detail = repository.get_run(run_id)
    assert detail is not None
    assert detail.case_results[0].turn_results[0].metric_results == metrics
