from collections.abc import Callable
from pathlib import Path

from app.evaluation.case_loader import load_evaluation_cases
from app.evaluation.comparison import compare_case_results
from app.evaluation.evaluator import ChainProtocol, evaluate_case
from app.evaluation.gates import evaluate_gates
from app.evaluation.metrics import summarize_case_results
from app.evaluation.models import (
    CaseResult,
    ComparisonResult,
    EvaluationCase,
    EvaluationOverview,
    EvaluationRunDetail,
    EvaluationRunSummary,
    TurnResult,
)
from app.evaluation.repository import EvaluationRepository
from app.rag.factory import create_rag_chain


class EvaluationService:
    # 注入仓库、Chain 工厂和评测集路径，让生产代码和测试代码可以共用同一套编排逻辑。
    def __init__(
        self,
        repository: EvaluationRepository,
        chain_factory: Callable[[], ChainProtocol],
        cases_path: Path,
        dialogues_path: Path,
        fail_under: float,
        max_p95_ms: float | None,
    ) -> None:
        self.repository = repository
        self.chain_factory = chain_factory
        self.cases_path = cases_path
        self.dialogues_path = dialogues_path
        self.fail_under = fail_under
        self.max_p95_ms = max_p95_ms

    # 加载单轮和连续对话评测用例，按配置决定是否包含连续对话。
    def _load_cases(self, include_dialogues: bool = True) -> list[EvaluationCase]:
        cases = load_evaluation_cases(self.cases_path)
        if include_dialogues:
            cases.extend(load_evaluation_cases(self.dialogues_path))
        return cases

    # 返回当前平台中的评测用例列表，供前端只读展示。
    def list_cases(self, include_dialogues: bool = True) -> list[EvaluationCase]:
        return self._load_cases(include_dialogues=include_dialogues)

    # 同步执行一次评测运行，并把结果保存为可追溯报告。
    def run_evaluation(
        self,
        include_dialogues: bool = True,
        include_load_test: bool = False,
    ) -> EvaluationRunDetail:
        chain = self.chain_factory()
        case_results = [evaluate_case(chain, case) for case in self._load_cases(include_dialogues=include_dialogues)]
        summary = summarize_case_results(case_results)
        gate_result = evaluate_gates(summary, fail_under=self.fail_under, max_p95_ms=self.max_p95_ms)
        self.repository.save_run(
            summary,
            case_results,
            gate_result,
            config={"include_dialogues": include_dialogues, "include_load_test": include_load_test},
        )
        loaded = self.repository.get_run(summary.run_id)
        if loaded is None:
            raise RuntimeError("评测运行已保存，但无法读取详情。")
        return loaded

    # 根据用例 ID 只执行一条评测用例，供前端逐条展示运行进度。
    def run_case(self, case_id: str, include_dialogues: bool = True) -> CaseResult | None:
        target_case = next(
            (case for case in self._load_cases(include_dialogues=include_dialogues) if case.id == case_id),
            None,
        )
        if target_case is None:
            return None
        return evaluate_case(self.chain_factory(), target_case)

    # 保存前端渐进式评测得到的用例结果，并生成完整运行报告。
    def save_case_results(self, case_results: list[CaseResult], config: dict | None = None) -> EvaluationRunDetail:
        summary = summarize_case_results(case_results)
        gate_result = evaluate_gates(summary, fail_under=self.fail_under, max_p95_ms=self.max_p95_ms)
        self.repository.save_run(summary, case_results, gate_result, config=config or {})
        loaded = self.repository.get_run(summary.run_id)
        if loaded is None:
            raise RuntimeError("评测运行已保存，但无法读取详情。")
        return loaded

    # 将 API 层传入的普通字典转换为 CaseResult 领域模型。
    def case_result_from_payload(self, payload: dict) -> CaseResult:
        return CaseResult(
            case_id=str(payload["case_id"]),
            category=str(payload["category"]),
            priority=str(payload["priority"]),
            case_type=str(payload["case_type"]),
            passed=bool(payload["passed"]),
            turn_results=[self.turn_result_from_payload(turn) for turn in payload.get("turn_results", [])],
            failure_reasons=list(payload.get("failure_reasons", [])),
            elapsed_ms=float(payload.get("elapsed_ms", 0)),
        )

    # 将 API 层传入的普通字典转换为 TurnResult 领域模型。
    def turn_result_from_payload(self, payload: dict) -> TurnResult:
        return TurnResult(
            question=str(payload["question"]),
            answer=str(payload["answer"]),
            standalone_question=payload.get("standalone_question"),
            passed=bool(payload["passed"]),
            keyword_passed=bool(payload["keyword_passed"]),
            source_passed=bool(payload["source_passed"]),
            image_passed=bool(payload["image_passed"]),
            no_answer_passed=bool(payload["no_answer_passed"]),
            matched_keywords=list(payload.get("matched_keywords", [])),
            missing_keywords=list(payload.get("missing_keywords", [])),
            matched_source_keywords=list(payload.get("matched_source_keywords", [])),
            missing_source_keywords=list(payload.get("missing_source_keywords", [])),
            forbidden_source_matches=list(payload.get("forbidden_source_matches", [])),
            sources=list(payload.get("sources", [])),
            image_count=int(payload.get("image_count", 0)),
            source_count=int(payload.get("source_count", 0)),
            elapsed_ms=float(payload.get("elapsed_ms", 0)),
            faithfulness_score=payload.get("faithfulness_score"),
            faithfulness_claims=list(payload.get("faithfulness_claims", [])),
            faithfulness_elapsed_ms=float(payload.get("faithfulness_elapsed_ms", 0.0)),
        )

    # 返回最近评测运行摘要列表，供前端历史列表使用。
    def list_runs(self, limit: int = 20) -> list[EvaluationRunSummary]:
        return self.repository.list_runs(limit=limit)

    # 根据运行 ID 返回完整评测报告。
    def get_run(self, run_id: str) -> EvaluationRunDetail | None:
        return self.repository.get_run(run_id)

    # 返回评测中心总览，包括最近一次运行和默认历史对比。
    def get_overview(self) -> EvaluationOverview:
        runs = self.repository.list_runs(limit=1)
        if not runs:
            return EvaluationOverview(latest=None, previous_run_id=None, comparison=None)

        latest = self.repository.get_run(runs[0].run_id)
        if latest is None:
            return EvaluationOverview(latest=None, previous_run_id=None, comparison=None)

        previous = self.repository.get_previous_completed_run(latest.summary.run_id)
        comparison = (
            compare_case_results(current=latest.case_results, baseline=previous.case_results)
            if previous is not None
            else None
        )
        return EvaluationOverview(
            latest=latest,
            previous_run_id=previous.summary.run_id if previous is not None else None,
            comparison=comparison,
        )

    # 对比某次运行和指定基准运行；未指定基准时自动使用上一条已完成运行。
    def compare_run(self, run_id: str, baseline_run_id: str | None = None) -> ComparisonResult | None:
        current = self.repository.get_run(run_id)
        if current is None:
            return None
        baseline = self.repository.get_run(baseline_run_id) if baseline_run_id else self.repository.get_previous_completed_run(run_id)
        if baseline is None:
            return None
        return compare_case_results(current=current.case_results, baseline=baseline.case_results)


# 根据应用配置创建评测服务实例，供 API 路由使用。
def create_evaluation_service() -> EvaluationService:
    from app.core.config import get_settings

    settings = get_settings()
    return EvaluationService(
        repository=EvaluationRepository(settings.evaluation_db_path),
        chain_factory=create_rag_chain,
        cases_path=settings.evaluation_cases_path,
        dialogues_path=settings.evaluation_dialogues_path,
        fail_under=settings.evaluation_fail_under,
        max_p95_ms=settings.evaluation_max_p95_ms,
    )
