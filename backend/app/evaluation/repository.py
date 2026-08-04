import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.evaluation.models import (
    CaseResult,
    EvaluationRunDetail,
    EvaluationRunSummary,
    GateResult,
    TurnResult,
)


class EvaluationRepository:
    # 保存评测数据库路径，SQLite 文件不存在时会在初始化或保存时创建。
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    # 打开数据库连接，并确保返回结果可以按字段名读取。
    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    # 初始化评测平台需要的三张表。
    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    case_total INTEGER NOT NULL,
                    case_passed INTEGER NOT NULL,
                    pass_rate REAL NOT NULL,
                    p0_total INTEGER NOT NULL,
                    p0_passed INTEGER NOT NULL,
                    avg_latency_ms REAL NOT NULL,
                    p95_latency_ms REAL NOT NULL,
                    gate_passed INTEGER NOT NULL,
                    gate_reasons_json TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS evaluation_case_results (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    case_type TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    turn_total INTEGER NOT NULL,
                    turn_passed INTEGER NOT NULL,
                    elapsed_ms REAL NOT NULL,
                    failure_reasons_json TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES evaluation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS evaluation_turn_results (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    case_result_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    standalone_question TEXT,
                    passed INTEGER NOT NULL,
                    keyword_passed INTEGER NOT NULL,
                    source_passed INTEGER NOT NULL,
                    image_passed INTEGER NOT NULL,
                    no_answer_passed INTEGER NOT NULL,
                    matched_keywords_json TEXT NOT NULL,
                    missing_keywords_json TEXT NOT NULL,
                    matched_source_keywords_json TEXT NOT NULL,
                    missing_source_keywords_json TEXT NOT NULL,
                    forbidden_source_matches_json TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    image_count INTEGER NOT NULL,
                    source_count INTEGER NOT NULL,
                    elapsed_ms REAL NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES evaluation_runs(id),
                    FOREIGN KEY(case_result_id) REFERENCES evaluation_case_results(id)
                );
                """
            )
            # 旧库兼容：为早期创建的库补齐语义评估新列，不丢历史数据。
            self._ensure_columns(connection)

    # 旧库兼容：检测缺失的语义评估列并用 ALTER TABLE 补齐，避免历史数据丢失。
    def _ensure_columns(self, connection: sqlite3.Connection) -> None:
        turn_columns = {
            "faithfulness_score": "REAL",
            "faithfulness_claims_json": "TEXT",
            "faithfulness_elapsed_ms": "REAL",
        }
        run_columns = {
            "avg_faithfulness_score": "REAL",
            "knowledge_base_id": "TEXT",
        }
        for table, columns in (("evaluation_turn_results", turn_columns), ("evaluation_runs", run_columns)):
            existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
            for column, decl in columns.items():
                if column not in existing:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")

    # 返回当前数据库中的表名，主要供测试和诊断使用。
    def list_table_names(self) -> list[str]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        return [str(row["name"]) for row in rows]

    # 将 Python 对象序列化为中文友好的 JSON 字符串。
    def _json(self, value: object) -> str:
        return json.dumps(value, ensure_ascii=False)

    # 计算一组用例行的单轮/多轮数量和分类通过率，用于恢复运行摘要中的明细指标。
    def _case_breakdowns(self, rows: list[sqlite3.Row]) -> dict[str, object]:
        single_rows = [row for row in rows if row["case_type"] == "single"]
        dialogue_rows = [row for row in rows if row["case_type"] == "dialogue"]
        category_rows: dict[str, list[sqlite3.Row]] = {}
        for row in rows:
            category_rows.setdefault(str(row["category"]), []).append(row)

        return {
            "single_total": len(single_rows),
            "single_passed": sum(1 for row in single_rows if row["passed"]),
            "dialogue_total": len(dialogue_rows),
            "dialogue_passed": sum(1 for row in dialogue_rows if row["passed"]),
            "category_pass_rates": {
                category: sum(1 for row in grouped_rows if row["passed"]) / len(grouped_rows)
                for category, grouped_rows in category_rows.items()
            },
        }

    # 保存一次完整评测运行，包括汇总、用例结果和每轮明细。
    def save_run(
        self,
        summary: EvaluationRunSummary,
        case_results: list[CaseResult],
        gate_result: GateResult,
        config: dict | None = None,
        error: str | None = None,
    ) -> str:
        self.initialize()
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO evaluation_runs (
                    id, status, started_at, finished_at, case_total, case_passed, pass_rate,
                    p0_total, p0_passed, avg_latency_ms, p95_latency_ms, gate_passed,
                    gate_reasons_json, config_json, error, avg_faithfulness_score, knowledge_base_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.run_id,
                    summary.status,
                    now,
                    now,
                    summary.case_total,
                    summary.case_passed,
                    summary.pass_rate,
                    summary.p0_total,
                    summary.p0_passed,
                    summary.avg_latency_ms,
                    summary.p95_latency_ms,
                    int(gate_result.passed),
                    self._json(gate_result.reasons),
                    self._json(config or {}),
                    error,
                    summary.avg_faithfulness_score,
                    summary.knowledge_base_id,
                ),
            )
            for case_result in case_results:
                case_result_id = f"case-result-{uuid4().hex}"
                connection.execute(
                    """
                    INSERT INTO evaluation_case_results (
                        id, run_id, case_id, category, priority, case_type, passed,
                        turn_total, turn_passed, elapsed_ms, failure_reasons_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case_result_id,
                        summary.run_id,
                        case_result.case_id,
                        case_result.category,
                        case_result.priority,
                        case_result.case_type,
                        int(case_result.passed),
                        len(case_result.turn_results),
                        sum(1 for turn in case_result.turn_results if turn.passed),
                        case_result.elapsed_ms,
                        self._json(case_result.failure_reasons),
                    ),
                )
                self._save_turn_results(connection, summary.run_id, case_result_id, case_result.turn_results)
        return summary.run_id

    # 保存某个用例下的所有轮次明细。
    def _save_turn_results(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        case_result_id: str,
        turn_results: list[TurnResult],
    ) -> None:
        for turn_index, turn in enumerate(turn_results, start=1):
            connection.execute(
                """
                INSERT INTO evaluation_turn_results (
                    id, run_id, case_result_id, turn_index, question, answer, standalone_question,
                    passed, keyword_passed, source_passed, image_passed, no_answer_passed,
                    matched_keywords_json, missing_keywords_json, matched_source_keywords_json,
                    missing_source_keywords_json, forbidden_source_matches_json, sources_json,
                    image_count, source_count, elapsed_ms,
                    faithfulness_score, faithfulness_claims_json, faithfulness_elapsed_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"turn-result-{uuid4().hex}",
                    run_id,
                    case_result_id,
                    turn_index,
                    turn.question,
                    turn.answer,
                    turn.standalone_question,
                    int(turn.passed),
                    int(turn.keyword_passed),
                    int(turn.source_passed),
                    int(turn.image_passed),
                    int(turn.no_answer_passed),
                    self._json(turn.matched_keywords),
                    self._json(turn.missing_keywords),
                    self._json(turn.matched_source_keywords),
                    self._json(turn.missing_source_keywords),
                    self._json(turn.forbidden_source_matches),
                    self._json(turn.sources),
                    turn.image_count,
                    turn.source_count,
                    turn.elapsed_ms,
                    turn.faithfulness_score,
                    self._json(turn.faithfulness_claims),
                    turn.faithfulness_elapsed_ms,
                ),
            )

    # 查询最近的评测运行摘要，默认用于前端运行列表。
    def list_runs(self, limit: int = 20) -> list[EvaluationRunSummary]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM evaluation_runs
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_summary(row, self._load_case_rows(connection, str(row["id"]))) for row in rows]

    # 查询某次评测运行的完整报告。
    def get_run(self, run_id: str) -> EvaluationRunDetail | None:
        self.initialize()
        with self._connect() as connection:
            run = connection.execute("SELECT * FROM evaluation_runs WHERE id = ?", (run_id,)).fetchone()
            if run is None:
                return None
            case_rows = self._load_case_rows(connection, run_id)
            case_results = [self._load_case_result(connection, case_row) for case_row in case_rows]
        return EvaluationRunDetail(
            summary=self._row_to_summary(run, case_rows),
            gate_result=GateResult(
                passed=bool(run["gate_passed"]),
                reasons=json.loads(run["gate_reasons_json"]),
            ),
            case_results=case_results,
        )

    # 查询指定运行之前最近一次已完成运行，用于默认历史对比。
    def get_previous_completed_run(self, run_id: str) -> EvaluationRunDetail | None:
        self.initialize()
        with self._connect() as connection:
            current = connection.execute("SELECT rowid FROM evaluation_runs WHERE id = ?", (run_id,)).fetchone()
            if current is None:
                return None
            previous = connection.execute(
                """
                SELECT id FROM evaluation_runs
                WHERE status = 'completed' AND rowid < ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (current["rowid"],),
            ).fetchone()
        return self.get_run(str(previous["id"])) if previous is not None else None

    # 把运行表中的一行转换成运行摘要模型。
    # 读取某次运行下的用例行，供详情和列表摘要复用。
    def _load_case_rows(self, connection: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
        return connection.execute(
            "SELECT * FROM evaluation_case_results WHERE run_id = ? ORDER BY rowid",
            (run_id,),
        ).fetchall()

    # 把运行表中的一行转换成运行摘要模型。
    def _row_to_summary(
        self,
        row: sqlite3.Row,
        case_rows: list[sqlite3.Row] | None = None,
    ) -> EvaluationRunSummary:
        breakdowns = self._case_breakdowns(case_rows or [])
        return EvaluationRunSummary(
            run_id=str(row["id"]),
            status=str(row["status"]),
            case_total=int(row["case_total"]),
            case_passed=int(row["case_passed"]),
            pass_rate=float(row["pass_rate"]),
            p0_total=int(row["p0_total"]),
            p0_passed=int(row["p0_passed"]),
            avg_latency_ms=float(row["avg_latency_ms"]),
            p95_latency_ms=float(row["p95_latency_ms"]),
            single_total=int(breakdowns["single_total"]),
            single_passed=int(breakdowns["single_passed"]),
            dialogue_total=int(breakdowns["dialogue_total"]),
            dialogue_passed=int(breakdowns["dialogue_passed"]),
            category_pass_rates=dict(breakdowns["category_pass_rates"]),
            avg_faithfulness_score=row["avg_faithfulness_score"],
            knowledge_base_id=row["knowledge_base_id"],
        )

    # 从数据库读取一个用例结果，并附带其所有轮次结果。
    def _load_case_result(self, connection: sqlite3.Connection, row: sqlite3.Row) -> CaseResult:
        turn_rows = connection.execute(
            "SELECT * FROM evaluation_turn_results WHERE case_result_id = ? ORDER BY turn_index",
            (row["id"],),
        ).fetchall()
        return CaseResult(
            case_id=str(row["case_id"]),
            category=str(row["category"]),
            priority=str(row["priority"]),
            case_type=str(row["case_type"]),
            passed=bool(row["passed"]),
            turn_results=[self._row_to_turn_result(turn_row) for turn_row in turn_rows],
            failure_reasons=json.loads(row["failure_reasons_json"]),
            elapsed_ms=float(row["elapsed_ms"]),
        )

    # 把轮次表中的一行转换成 TurnResult。
    def _row_to_turn_result(self, row: sqlite3.Row) -> TurnResult:
        return TurnResult(
            question=str(row["question"]),
            answer=str(row["answer"]),
            standalone_question=row["standalone_question"],
            passed=bool(row["passed"]),
            keyword_passed=bool(row["keyword_passed"]),
            source_passed=bool(row["source_passed"]),
            image_passed=bool(row["image_passed"]),
            no_answer_passed=bool(row["no_answer_passed"]),
            matched_keywords=json.loads(row["matched_keywords_json"]),
            missing_keywords=json.loads(row["missing_keywords_json"]),
            matched_source_keywords=json.loads(row["matched_source_keywords_json"]),
            missing_source_keywords=json.loads(row["missing_source_keywords_json"]),
            forbidden_source_matches=json.loads(row["forbidden_source_matches_json"]),
            sources=json.loads(row["sources_json"]),
            image_count=int(row["image_count"]),
            source_count=int(row["source_count"]),
            elapsed_ms=float(row["elapsed_ms"]),
            faithfulness_score=row["faithfulness_score"],
            faithfulness_claims=json.loads(row["faithfulness_claims_json"]) if row["faithfulness_claims_json"] else [],
            faithfulness_elapsed_ms=float(row["faithfulness_elapsed_ms"] or 0.0),
        )
