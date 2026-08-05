import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Sequence

from app.core.config import REPO_ROOT, get_settings
from app.evaluation.case_loader import load_evaluation_suite
from app.evaluation.gates import GateThresholds, evaluate_absolute_gate, evaluate_regression_gate
from app.evaluation.judge import create_judgement_client
from app.evaluation.models import EvaluationRunDetail, GateMode, RunStatus
from app.evaluation.repository import EvaluationRepository
from app.evaluation.runner import EvaluationRunner
from app.evaluation.snapshot import build_run_snapshot
from app.evaluation.suite import EvaluationSuite
from app.rag.factory import create_rag_chain

DEFAULT_REPORT_PATH = REPO_ROOT / "storage" / "reports" / "evaluation-gate.json"


@dataclass(frozen=True)
class GateDependencies:
    repository: EvaluationRepository
    suite: EvaluationSuite
    runner: EvaluationRunner
    snapshot: dict


def _load_suite(suite_id: str, paths: tuple[Path, Path]) -> EvaluationSuite:
    for path in paths:
        if path.exists():
            suite = load_evaluation_suite(path)
            if suite.id == suite_id:
                return suite
    raise ValueError(f"unknown evaluation suite: {suite_id}")


def build_gate_dependencies(suite_id: str) -> GateDependencies:
    """Build the same trusted local execution stack used by evaluation service."""
    settings = get_settings()
    suite = _load_suite(suite_id, (settings.evaluation_cases_path, settings.evaluation_dialogues_path))
    repository = EvaluationRepository(settings.evaluation_db_path)
    runner = EvaluationRunner(
        repository=repository,
        chain_factory=create_rag_chain,
        judge_factory=lambda: create_judgement_client(settings) if settings.evaluation_semantic_enabled else None,
        metric_names=tuple(name.strip() for name in settings.evaluation_metrics.split(",") if name.strip()),
        price_rates=settings.evaluation_price_rates,
        max_p95_ms=settings.evaluation_max_p95_ms,
    )
    return GateDependencies(
        repository=repository,
        suite=suite,
        runner=runner,
        snapshot=build_run_snapshot(settings, suite).model_dump(mode="json"),
    )


def _decision_payload(decision) -> dict[str, object]:
    return {
        "outcome": decision.outcome.value,
        "reasons": [
            *decision.validity_reasons,
            *decision.absolute_reasons,
            *decision.regression_reasons,
        ],
    }


def _status_value(status: str | RunStatus) -> str:
    return status.value if isinstance(status, RunStatus) else str(status)


def _redacted_snapshot(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _redacted_snapshot(item)
            for key, item in value.items()
            if not any(marker in key.lower() for marker in ("api_key", "authorization", "secret", "token"))
        }
    if isinstance(value, list):
        return [_redacted_snapshot(item) for item in value]
    return value


def _build_report(
    detail: EvaluationRunDetail,
    suite: EvaluationSuite,
    mode: GateMode,
    baseline_run_id: str | None,
    snapshot: dict,
    absolute,
    regression,
) -> dict[str, object]:
    failed_case_ids = [case.case_id for case in detail.case_results if not case.passed]
    return {
        "run_id": detail.summary.run_id,
        "suite": {"id": suite.id, "version": suite.version},
        "snapshot": _redacted_snapshot(snapshot),
        "status": _status_value(detail.summary.status),
        "mode": mode.value.lower(),
        "baseline_run_id": baseline_run_id,
        "gate_passed": detail.gate_result.passed,
        "gate_reasons": detail.gate_result.reasons,
        "absolute_gate": _decision_payload(absolute),
        "regression_gate": _decision_payload(regression) if regression is not None else None,
        "failed_case_ids": failed_case_ids,
        "token_count": detail.summary.total_token_count,
        "estimated_cost": detail.summary.estimated_cost,
    }


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _print_detail(detail: EvaluationRunDetail, suite: EvaluationSuite, baseline_run_id: str | None, output: Path, absolute, regression) -> None:
    for case in detail.case_results:
        print(f"Case {case.case_id}: {'passed' if case.passed else 'failed'}")
    failed_case_ids = [case.case_id for case in detail.case_results if not case.passed]
    print(f"Run ID: {detail.summary.run_id}")
    print(f"Suite: {suite.id}@{suite.version}")
    print(f"Baseline: {baseline_run_id or 'none'}")
    print(f"Failures: {', '.join(failed_case_ids) or 'none'}")
    print(f"Absolute gate: {absolute.outcome.value}")
    print(f"Regression gate: {regression.outcome.value if regression is not None else 'not run'}")
    print(f"Tokens/cost: {detail.summary.total_token_count}/{detail.summary.estimated_cost}")
    print(f"Report: {output}")


def _exit_code(mode: GateMode, detail: EvaluationRunDetail, absolute, regression) -> int:
    if _status_value(detail.summary.status).lower() != RunStatus.COMPLETED.value:
        return 2
    if absolute.outcome.value == "INVALID" or (regression is not None and regression.outcome.value == "INVALID"):
        return 2
    if mode == GateMode.CALIBRATION:
        return 0
    if absolute.outcome.value == "FAILED" or (regression is not None and regression.outcome.value == "FAILED"):
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local RAG evaluation release gate")
    parser.add_argument("--suite", default="core")
    parser.add_argument("--mode", choices=("calibration", "blocking"), default="blocking")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--approve-baseline", action="store_true")
    parser.add_argument("--approved-by")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.approved_by and not args.approve_baseline:
        print("--approved-by requires --approve-baseline", file=sys.stderr)
        return 2
    if args.approve_baseline and (not args.approved_by or not args.approved_by.strip()):
        print("--approve-baseline requires --approved-by", file=sys.stderr)
        return 2
    if args.approve_baseline and args.mode != "calibration":
        print("--approve-baseline is only valid in calibration mode", file=sys.stderr)
        return 2

    try:
        dependencies = build_gate_dependencies(args.suite)
        mode = GateMode(args.mode.upper())
        baseline_run_id = dependencies.repository.get_current_baseline(dependencies.suite.id)
        if mode == GateMode.BLOCKING and baseline_run_id is None:
            print("blocking mode requires an approved baseline", file=sys.stderr)
            return 2
        run_id = dependencies.repository.create_run(
            dependencies.suite.id,
            dependencies.suite.version,
            str(dependencies.snapshot["suite_hash"]),
            dependencies.snapshot,
            mode.value,
            case_total=len(dependencies.suite.cases),
        )
        detail = dependencies.runner.run(run_id, dependencies.suite, mode, Event())
        thresholds = GateThresholds(
            mode=mode,
            min_pass_rate=0.85,
            min_avg_correctness_score=dependencies.suite.default_thresholds.answer_correctness,
            min_avg_fact_coverage_score=dependencies.suite.default_thresholds.p1_required_fact_coverage,
            min_avg_faithfulness_score=dependencies.suite.default_thresholds.faithfulness,
        )
        absolute = evaluate_absolute_gate(detail.summary, thresholds)
        baseline = dependencies.repository.get_run(baseline_run_id) if baseline_run_id else None
        regression = evaluate_regression_gate(detail, baseline, thresholds) if baseline is not None else None
        report = _build_report(detail, dependencies.suite, mode, baseline_run_id, dependencies.snapshot, absolute, regression)
        _write_report(args.output, report)
        _print_detail(detail, dependencies.suite, baseline_run_id, args.output, absolute, regression)
        if args.approve_baseline:
            if _exit_code(mode, detail, absolute, regression) != 0:
                print("only a valid passing calibration run can be approved", file=sys.stderr)
                return 2
            dependencies.repository.approve_baseline(detail.summary.run_id, args.approved_by.strip())
        return _exit_code(mode, detail, absolute, regression)
    except Exception as exc:
        print(f"evaluation gate failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
