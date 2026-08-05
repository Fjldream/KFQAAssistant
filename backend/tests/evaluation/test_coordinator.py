from threading import Event

import pytest

from app.evaluation.models import GateMode


class BlockingRunner:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()
        self.cancel: Event | None = None

    def run(self, run_id, suite, mode, cancel):
        self.cancel = cancel
        self.started.set()
        self.release.wait(timeout=2)


def test_coordinator_rejects_second_active_run_and_releases_after_completion():
    from app.evaluation.coordinator import EvaluationCoordinator, EvaluationRunConflict

    runner = BlockingRunner()
    created: list[str] = []
    coordinator = EvaluationCoordinator(
        runner=runner,
        load_suite=lambda suite_id: {"id": suite_id},
        create_run=lambda suite, mode: created.append("run-1") or "run-1",
    )
    try:
        assert coordinator.start("core", GateMode.CALIBRATION) == "run-1"
        assert runner.started.wait(timeout=1)
        with pytest.raises(EvaluationRunConflict):
            coordinator.start("core", GateMode.CALIBRATION)

        runner.release.set()
        coordinator.wait_for_idle(timeout=1)

        assert coordinator.start("core", GateMode.CALIBRATION) == "run-1"
    finally:
        runner.release.set()
        coordinator.shutdown()


def test_coordinator_cancel_sets_active_run_event():
    from app.evaluation.coordinator import EvaluationCoordinator

    runner = BlockingRunner()
    coordinator = EvaluationCoordinator(runner, lambda _: {"id": "core"}, lambda suite, mode: "run-1")
    try:
        coordinator.start("core", GateMode.CALIBRATION)
        assert runner.started.wait(timeout=1)

        assert coordinator.cancel("run-1") is True
        assert runner.cancel is not None and runner.cancel.is_set()
        assert coordinator.cancel("unknown") is False
    finally:
        runner.release.set()
        coordinator.shutdown()


def test_coordinator_shutdown_does_not_abandon_already_started_run():
    from app.evaluation.coordinator import EvaluationCoordinator

    runner = BlockingRunner()
    coordinator = EvaluationCoordinator(runner, lambda _: {"id": "core"}, lambda suite, mode: "run-1")
    coordinator.start("core", GateMode.CALIBRATION)
    assert runner.started.wait(timeout=1)

    coordinator.shutdown()

    assert runner.cancel is not None
    runner.release.set()


def test_coordinator_releases_an_immediately_completed_run():
    from app.evaluation.coordinator import EvaluationCoordinator

    class ImmediateRunner:
        def run(self, run_id, suite, mode, cancel):
            return None

    coordinator = EvaluationCoordinator(ImmediateRunner(), lambda _: {"id": "core"}, lambda suite, mode: "run-1")
    try:
        coordinator.start("core", GateMode.CALIBRATION)
        assert coordinator.wait_for_idle(timeout=1)
        assert coordinator.start("core", GateMode.CALIBRATION) == "run-1"
    finally:
        coordinator.shutdown()
