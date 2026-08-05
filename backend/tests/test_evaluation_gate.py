import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.evaluation_gate as gate_module
from app.evaluation.models import CaseResult, EvaluationRunDetail, EvaluationRunSummary, GateResult, RunStatus, TurnResult


@dataclass
class FakeSuite:
    id: str = "core"
    version: str = "v1"
    cases: tuple[str, ...] = ("case-1",)

    @property
    def default_thresholds(self):
        return SimpleNamespace(answer_correctness=0.8, faithfulness=0.9, p1_required_fact_coverage=0.8)


class FakeRepository:
    def __init__(self, baseline_id: str | None = "baseline-1") -> None:
        self.baseline_id = baseline_id
        self.created: list[tuple] = []
        self.approvals: list[tuple[str, str]] = []

    def get_current_baseline(self, suite_id: str) -> str | None:
        assert suite_id == "core"
        return self.baseline_id

    def create_run(self, *args, **kwargs) -> str:
        self.created.append((args, kwargs))
        return "run-local-1"

    def approve_baseline(self, run_id: str, approved_by: str) -> None:
        self.approvals.append((run_id, approved_by))

    def get_run(self, run_id: str) -> EvaluationRunDetail:
        return _detail(status="completed", gate_passed=True)


class FakeRunner:
    def __init__(self) -> None:
        self.detail = _detail()
        self.calls: list[tuple] = []

    def result(self, *, status: str, gate_passed: bool) -> None:
        self.detail = _detail(status=status, gate_passed=gate_passed)

    def run(self, *args):
        self.calls.append(args)
        return self.detail


def _detail(status: str = "completed", gate_passed: bool = True) -> EvaluationRunDetail:
    case = CaseResult(
        case_id="case-1",
        category="core",
        priority="P0",
        case_type="single",
        passed=False,
        turn_results=[
            TurnResult(
                question="question",
                answer="answer",
                standalone_question="question",
                passed=False,
                keyword_passed=False,
                source_passed=True,
                image_passed=True,
                no_answer_passed=True,
            )
        ],
        failure_reasons=["required fact missing"],
    )
    return EvaluationRunDetail(
        summary=EvaluationRunSummary(
            run_id="run-local-1",
            status=status,
            case_total=1,
            case_passed=0,
            pass_rate=0.0,
            p0_total=1,
            p0_passed=0,
            total_token_count=17,
            estimated_cost=0.0025,
        ),
        gate_result=GateResult(passed=gate_passed, reasons=["required fact missing"]),
        case_results=[case],
    )


@pytest.fixture
def fake_runner(monkeypatch):
    repository = FakeRepository()
    runner = FakeRunner()
    dependencies = gate_module.GateDependencies(
        repository=repository, suite=FakeSuite(), runner=runner, snapshot={"suite_hash": "hash"}
    )
    monkeypatch.setattr(gate_module, "build_gate_dependencies", lambda suite_id: dependencies)
    return runner


@pytest.mark.parametrize(("mode", "status", "gate_passed", "expected"), [
    ("calibration", "completed", False, 0),
    ("blocking", "completed", True, 0),
    ("blocking", "completed", False, 1),
    ("blocking", "invalid", False, 2),
])
def test_gate_exit_codes(fake_runner, mode, status, gate_passed, expected):
    fake_runner.result(status=status, gate_passed=gate_passed)

    assert gate_module.main(["--suite", "core", "--mode", mode]) == expected


def test_gate_accepts_completed_runner_status_enum(fake_runner):
    fake_runner.result(status=RunStatus.COMPLETED, gate_passed=True)

    assert gate_module.main(["--suite", "core", "--mode", "blocking"]) == 0


def test_gate_writes_redacted_json_report_and_prints_run_summary(tmp_path: Path, fake_runner, capsys):
    output = tmp_path / "reports" / "gate.json"

    assert gate_module.main(["--suite", "core", "--mode", "blocking", "--output", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    captured = capsys.readouterr()
    assert payload["run_id"] == "run-local-1"
    assert payload["suite"] == {"id": "core", "version": "v1"}
    assert payload["baseline_run_id"] == "baseline-1"
    assert payload["failed_case_ids"] == ["case-1"]
    assert "Run ID: run-local-1" in captured.out
    assert "Suite: core@v1" in captured.out
    assert "Baseline: baseline-1" in captured.out
    assert "Failures: case-1" in captured.out
    assert f"Report: {output}" in captured.out


def test_blocking_mode_without_approved_baseline_returns_two(monkeypatch, capsys):
    repository = FakeRepository(baseline_id=None)
    runner = FakeRunner()
    dependencies = gate_module.GateDependencies(
        repository=repository, suite=FakeSuite(), runner=runner, snapshot={"suite_hash": "hash"}
    )
    monkeypatch.setattr(gate_module, "build_gate_dependencies", lambda suite_id: dependencies)

    assert gate_module.main(["--suite", "core", "--mode", "blocking"]) == 2
    assert runner.calls == []
    assert "approved baseline" in capsys.readouterr().err


def test_gate_never_emits_settings_secrets(monkeypatch, tmp_path: Path, capsys):
    repository = FakeRepository()
    dependencies = gate_module.GateDependencies(
        repository=repository,
        suite=FakeSuite(),
        runner=FakeRunner(),
        snapshot={"suite_hash": "hash", "deepseek_api_key": "super-secret-value"},
    )
    monkeypatch.setattr(gate_module, "build_gate_dependencies", lambda suite_id: dependencies)
    output = tmp_path / "gate.json"

    assert gate_module.main(["--suite", "core", "--mode", "calibration", "--output", str(output)]) == 0

    assert "super-secret-value" not in output.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "super-secret-value" not in captured.out
    assert "super-secret-value" not in captured.err


def test_approver_requires_explicit_baseline_approval_flag(fake_runner, capsys):
    assert gate_module.main(["--suite", "core", "--mode", "calibration", "--approved-by", "release"]) == 2
    assert "--approve-baseline" in capsys.readouterr().err
