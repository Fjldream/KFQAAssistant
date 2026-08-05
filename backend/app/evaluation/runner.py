from dataclasses import replace
from decimal import Decimal
from threading import Event
from typing import Callable

from app.evaluation.costs import estimate_deepseek_cost
from app.evaluation.evaluator import ChainProtocol, evaluate_case
from app.evaluation.gates import GateThresholds, evaluate_absolute_gate, evaluate_regression_gate, evaluate_run_validity
from app.evaluation.metrics import summarize_case_results
from app.evaluation.models import (
    CaseResult,
    EvaluationCase,
    EvaluationRunDetail,
    EvaluationTurn,
    GateMode,
    GateOutcome,
    GateResult,
    MetricResult,
    MetricStatus,
    RunStatus,
    TurnResult,
)
from app.evaluation.repository import EvaluationRepository
from app.evaluation.suite import EvaluationCaseSpec, EvaluationSuite
from app.observability.model_usage import ModelUsageEvent, capture_model_usage


def _legacy_case(case: EvaluationCaseSpec) -> EvaluationCase:
    return EvaluationCase(
        id=case.id,
        category=case.category,
        priority=case.priority,
        tags=case.tags,
        turns=[
            EvaluationTurn(
                question=turn.question,
                expected_keywords=turn.keyword_anchors,
                expect_images=turn.expect_images,
                expect_no_answer=turn.expect_no_answer,
                min_sources=turn.min_sources,
                min_images=turn.min_images,
                reference_answer=turn.reference_answer,
                required_facts=[fact.model_dump() for fact in turn.required_facts],
                keyword_anchors=turn.keyword_anchors,
                forbidden_facts=turn.forbidden_facts,
                expected_source_ids=turn.expected_source_ids,
                expected_chunk_ids=turn.expected_chunk_ids,
                forbidden_source_ids=turn.forbidden_source_ids,
            )
            for turn in case.turns
        ],
    )


def _case_error(case: EvaluationCase, code: str) -> CaseResult:
    metric = MetricResult("runner", None, MetricStatus.ERROR, error_code=code)
    turn = TurnResult(
        question=case.turns[0].question,
        answer="",
        standalone_question=None,
        passed=False,
        keyword_passed=False,
        source_passed=False,
        image_passed=False,
        no_answer_passed=False,
        metric_results=[metric],
    )
    return CaseResult(
        case_id=case.id,
        category=case.category,
        priority=case.priority,
        case_type=case.case_type,
        passed=False,
        turn_results=[turn],
        failure_reasons=[f"runner error: {code}"],
    )


class EvaluationRunner:
    """Runs only server-owned suite cases and persists each completed case atomically."""

    def __init__(
        self,
        repository: EvaluationRepository,
        chain_factory: Callable[[], ChainProtocol],
        judge_factory: Callable[[], object | None],
        metric_names: tuple[str, ...],
        price_rates: dict[str, str] | None = None,
        max_p95_ms: float | None = 30_000.0,
    ) -> None:
        self.repository = repository
        self.chain_factory = chain_factory
        self.judge_factory = judge_factory
        self.metric_names = metric_names
        self.price_rates = price_rates or {}
        self.max_p95_ms = max_p95_ms

    def run(self, run_id: str, suite: EvaluationSuite, mode: GateMode, cancel: Event) -> EvaluationRunDetail:
        if not suite.cases:
            raise ValueError("an evaluation suite must contain at least one case")

        self.repository.transition_run(run_id, RunStatus.RUNNING)
        chain = self.chain_factory()
        judge = self.judge_factory()
        case_results: list[CaseResult] = []
        all_events: list[ModelUsageEvent] = []

        for spec in suite.cases:
            if cancel.is_set():
                return self._cancel(run_id, case_results, all_events)
            case = _legacy_case(spec)
            try:
                with capture_model_usage() as collector:
                    result = evaluate_case(chain, case, judge=judge, semantic_enabled=True, metrics=self.metric_names)
                events = list(collector.events)
                result = self._attach_usage(result, events)
                all_events.extend(events)
            except Exception as exc:
                result = _case_error(case, type(exc).__name__)
            self.repository.save_case_result(run_id, result)
            case_results.append(result)
            if cancel.is_set():
                return self._cancel(run_id, case_results, all_events)

        summary = replace(summarize_case_results(case_results), run_id=run_id)
        self.repository.transition_run(run_id, RunStatus.SCORING)
        validity = evaluate_run_validity(summary)
        thresholds = GateThresholds(
            mode=mode,
            min_pass_rate=0.85,
            min_avg_correctness_score=suite.default_thresholds.answer_correctness,
            min_avg_fact_coverage_score=suite.default_thresholds.p1_required_fact_coverage,
            min_avg_faithfulness_score=suite.default_thresholds.faithfulness,
            max_p95_latency_ms=self.max_p95_ms,
        )
        absolute = evaluate_absolute_gate(summary, thresholds)
        reasons = [*validity.validity_reasons, *absolute.absolute_reasons]
        decision = absolute
        detail = EvaluationRunDetail(replace(summary, status=RunStatus.COMPLETED), GateResult(True, reasons), case_results)
        baseline_id = self.repository.get_current_baseline(suite.id)
        if baseline_id is not None:
            baseline = self.repository.get_run(baseline_id)
            if baseline is not None:
                baseline_metadata = self.repository.get_run_metadata(baseline_id)
                current_metadata = self.repository.get_run_metadata(run_id)
                if baseline_metadata is None or current_metadata is None or any(
                    baseline_metadata[field] != current_metadata[field]
                    for field in ("suite_id", "suite_version", "suite_hash")
                ):
                    reasons.append("批准基准 Suite 版本或内容哈希不匹配")
                    decision = GateDecision(GateOutcome.INVALID, validity_reasons=[reasons[-1]])
                else:
                    regression = evaluate_regression_gate(detail, baseline, thresholds)
                    reasons.extend(regression.validity_reasons)
                    reasons.extend(regression.regression_reasons)
                    decision = regression if regression.outcome == GateOutcome.INVALID else decision
                    if regression.outcome == GateOutcome.FAILED:
                        decision = regression

        gate = GateResult(
            passed=decision.outcome == GateOutcome.PASSED and validity.outcome != GateOutcome.INVALID,
            reasons=reasons,
        )
        token_totals = {
            "cache_hit": sum(event.cache_hit_tokens for event in all_events),
            "cache_miss": sum(max(0, event.prompt_tokens - event.cache_hit_tokens) for event in all_events),
            "output": sum(event.completion_tokens for event in all_events),
        }
        cost = estimate_deepseek_cost(all_events, self.price_rates)
        if validity.outcome == GateOutcome.INVALID or decision.outcome == GateOutcome.INVALID:
            self.repository.invalidate_run(
                run_id,
                "evaluation_invalid",
                summary,
                gate,
                token_totals=token_totals,
                estimated_cost=str(cost),
            )
            return self.repository.get_run(run_id) or EvaluationRunDetail(replace(summary, status=RunStatus.INVALID), gate, case_results)

        self.repository.finish_run(
            run_id,
            replace(summary, status=RunStatus.COMPLETED),
            gate,
            token_totals=token_totals,
            estimated_cost=str(cost),
        )
        return self.repository.get_run(run_id) or EvaluationRunDetail(replace(summary, status=RunStatus.COMPLETED), gate, case_results)

    def _attach_usage(self, result: CaseResult, events: list[ModelUsageEvent]) -> CaseResult:
        payload = {
            "events": [event.__dict__ for event in events],
            "total_tokens": sum(event.prompt_tokens + event.completion_tokens for event in events),
        }
        return replace(result, metric_results=[*result.metric_results, MetricResult("model_usage", None, MetricStatus.SKIPPED, token_usage=payload)])

    def _cancel(
        self,
        run_id: str,
        case_results: list[CaseResult],
        events: list[ModelUsageEvent],
    ) -> EvaluationRunDetail:
        summary = replace(summarize_case_results(case_results), run_id=run_id, status=RunStatus.CANCELLED)
        gate = GateResult(False, ["evaluation cancelled"])
        self.repository.cancel_run(
            run_id,
            summary,
            gate,
            token_totals={
                "cache_hit": sum(event.cache_hit_tokens for event in events),
                "cache_miss": sum(max(0, event.prompt_tokens - event.cache_hit_tokens) for event in events),
                "output": sum(event.completion_tokens for event in events),
            },
            estimated_cost=str(estimate_deepseek_cost(events, self.price_rates)),
        )
        return EvaluationRunDetail(summary, gate, case_results)
