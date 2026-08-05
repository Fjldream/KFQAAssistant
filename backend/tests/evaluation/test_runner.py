from dataclasses import dataclass
from pathlib import Path
from threading import Event

import pytest

from app.evaluation.models import GateMode, MetricStatus, RunStatus
from app.evaluation.repository import EvaluationRepository
from app.evaluation.suite import EvaluationSuite
from app.observability.model_usage import record_model_usage
from app.schemas.chat import ChatResponse, SourceSnippet


def core_suite(two_cases: bool = False) -> EvaluationSuite:
    cases = [
        {
            "id": "case-1",
            "category": "core",
            "priority": "P0",
            "question": "How do I create a project?",
            "required_facts": [{"id": "create", "text": "Create a project"}],
        }
    ]
    if two_cases:
        cases.append(
            {
                "id": "case-2",
                "category": "core",
                "priority": "P1",
                "question": "How do I save it?",
                "required_facts": [{"id": "save", "text": "Save the project"}],
            }
        )
    return EvaluationSuite.model_validate(
        {
            "id": "core",
            "version": "v1",
            "default_thresholds": {
                "answer_correctness": 0.8,
                "faithfulness": 0.8,
                "p1_required_fact_coverage": 0.8,
            },
            "cases": cases,
        }
    )


class FakeChain:
    def __init__(self, fail_question: str | None = None, cancel: Event | None = None) -> None:
        self.fail_question = fail_question
        self.cancel = cancel
        self.calls: list[str] = []

    def answer(self, question, conversation_summary="", conversation_turn_count=0, recent_messages=None):
        self.calls.append(question)
        if self.cancel is not None and len(self.calls) == 1:
            self.cancel.set()
        if question == self.fail_question:
            raise RuntimeError("rag timeout")
        record_model_usage("answer", "test-model", {"prompt_tokens": 10, "completion_tokens": 4})
        return ChatResponse(
            answer="Create a project, then save the project.",
            sources=[SourceSnippet(title="guide", source_path="guide.md", snippet="Create and save the project.")],
            standalone_question=question,
        )


class FakeJudge:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def complete_json(self, system_prompt, user_prompt):
        if self.error is not None:
            raise self.error
        record_model_usage("judge", "test-judge", {"prompt_tokens": 6, "completion_tokens": 2})
        if "correctness" in system_prompt:
            return {
                "correctness": 1.0,
                "relevance": 1.0,
                "facts": [{"id": "create" if "create" in user_prompt else "save", "covered": True}],
                "forbidden_fact_matches": [],
            }
        return {"claims": [{"claim": "Create a project", "supported": True, "evidence": "guide"}]}


@dataclass
class Dependencies:
    repository: EvaluationRepository
    runner: object
    judge: FakeJudge


@pytest.fixture
def valid_dependencies(tmp_path: Path) -> Dependencies:
    from app.evaluation.runner import EvaluationRunner

    repository = EvaluationRepository(tmp_path / "eval.db")
    judge = FakeJudge()
    runner = EvaluationRunner(
        repository=repository,
        chain_factory=FakeChain,
        judge_factory=lambda: judge,
        metric_names=("answer_correctness", "required_fact_coverage", "faithfulness"),
    )
    return Dependencies(repository, runner, judge)


def create_run(repository: EvaluationRepository, suite: EvaluationSuite) -> str:
    return repository.create_run(suite.id, suite.version, "suite-hash", {"suite_id": suite.id}, "CALIBRATION", case_total=len(suite.cases))


def test_runner_checkpoints_each_case_and_completes(valid_dependencies: Dependencies):
    suite = core_suite(two_cases=True)
    run_id = create_run(valid_dependencies.repository, suite)

    detail = valid_dependencies.runner.run(run_id, suite, GateMode.CALIBRATION, Event())

    assert detail.summary.status == RunStatus.COMPLETED
    assert valid_dependencies.repository.get_run(run_id).summary.completed_case_count == 2


def test_runner_marks_invalid_when_judge_errors(valid_dependencies: Dependencies):
    from app.evaluation.judge import JudgementError

    suite = core_suite()
    valid_dependencies.judge.error = JudgementError("timeout")
    run_id = create_run(valid_dependencies.repository, suite)

    detail = valid_dependencies.runner.run(run_id, suite, GateMode.CALIBRATION, Event())

    assert detail.summary.status == RunStatus.INVALID
    assert detail.gate_result.reasons


def test_runner_stops_after_checkpoint_when_cancelled(tmp_path: Path):
    from app.evaluation.runner import EvaluationRunner

    suite = core_suite(two_cases=True)
    cancel = Event()
    repository = EvaluationRepository(tmp_path / "eval.db")
    runner = EvaluationRunner(
        repository=repository,
        chain_factory=lambda: FakeChain(cancel=cancel),
        judge_factory=FakeJudge,
        metric_names=("answer_correctness", "required_fact_coverage", "faithfulness"),
    )
    run_id = create_run(repository, suite)

    detail = runner.run(run_id, suite, GateMode.CALIBRATION, cancel)

    assert detail.summary.status == RunStatus.CANCELLED
    assert repository.get_run(run_id).summary.completed_case_count == 1


def test_runner_checkpoints_rag_failure_and_continues_remaining_cases(tmp_path: Path):
    from app.evaluation.runner import EvaluationRunner

    suite = core_suite(two_cases=True)
    repository = EvaluationRepository(tmp_path / "eval.db")
    runner = EvaluationRunner(
        repository=repository,
        chain_factory=lambda: FakeChain(fail_question="How do I create a project?"),
        judge_factory=FakeJudge,
        metric_names=("answer_correctness", "required_fact_coverage", "faithfulness"),
    )
    run_id = create_run(repository, suite)

    detail = runner.run(run_id, suite, GateMode.CALIBRATION, Event())

    assert detail.summary.status == RunStatus.INVALID
    assert [case.case_id for case in detail.case_results] == ["case-1", "case-2"]
    assert detail.case_results[0].turn_results[0].metric_results[0].status == MetricStatus.ERROR


def test_runner_rejects_empty_suite_before_creating_chain(tmp_path: Path):
    from app.evaluation.runner import EvaluationRunner

    suite = core_suite()
    suite.cases.clear()
    repository = EvaluationRepository(tmp_path / "eval.db")
    runner = EvaluationRunner(repository, lambda: (_ for _ in ()).throw(AssertionError("chain created")), FakeJudge, ())
    run_id = repository.create_run(suite.id, suite.version, "suite-hash", {}, "CALIBRATION", case_total=1)

    with pytest.raises(ValueError, match="at least one case"):
        runner.run(run_id, suite, GateMode.CALIBRATION, Event())


def test_runner_attaches_captured_usage_to_its_case(valid_dependencies: Dependencies):
    suite = core_suite()
    run_id = create_run(valid_dependencies.repository, suite)

    detail = valid_dependencies.runner.run(run_id, suite, GateMode.CALIBRATION, Event())

    usage = next(metric for metric in detail.case_results[0].metric_results if metric.name == "model_usage")
    assert usage.token_usage["events"] == [
        {"operation": "answer", "model": "test-model", "prompt_tokens": 10, "completion_tokens": 4, "cache_hit_tokens": 0},
        {"operation": "judge", "model": "test-judge", "prompt_tokens": 6, "completion_tokens": 2, "cache_hit_tokens": 0},
        {"operation": "judge", "model": "test-judge", "prompt_tokens": 6, "completion_tokens": 2, "cache_hit_tokens": 0},
    ]


def test_runner_uses_a_valid_approved_baseline(valid_dependencies: Dependencies):
    suite = core_suite()
    baseline_id = create_run(valid_dependencies.repository, suite)
    valid_dependencies.runner.run(baseline_id, suite, GateMode.CALIBRATION, Event())
    valid_dependencies.repository.approve_baseline(baseline_id)
    run_id = create_run(valid_dependencies.repository, suite)

    detail = valid_dependencies.runner.run(run_id, suite, GateMode.CALIBRATION, Event())

    assert detail.summary.status == RunStatus.COMPLETED
    assert not any(reason.startswith("批准基准无效") for reason in detail.gate_result.reasons)
