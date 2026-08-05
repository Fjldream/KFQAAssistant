from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event, RLock
from time import monotonic, sleep
from typing import Callable

from app.evaluation.models import GateMode
from app.evaluation.runner import EvaluationRunner
from app.evaluation.suite import EvaluationSuite


class EvaluationRunConflict(RuntimeError):
    pass


class EvaluationCoordinator:
    """Serializes SQLite evaluation runs while allowing callers to poll their persisted state."""

    def __init__(
        self,
        runner: EvaluationRunner,
        load_suite: Callable[[str], EvaluationSuite],
        create_run: Callable[[EvaluationSuite, GateMode], str],
        request_cancel: Callable[[str], bool] | None = None,
    ) -> None:
        self.runner = runner
        self.load_suite = load_suite
        self.create_run = create_run
        self.request_cancel = request_cancel
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="evaluation-runner")
        self._lock = RLock()
        self._active: tuple[str, Event, Future[object]] | None = None

    def start(self, suite_id: str, mode: GateMode) -> str:
        with self._lock:
            if self._active is not None:
                raise EvaluationRunConflict("an evaluation run is already active")
            suite = self.load_suite(suite_id)
            run_id = self.create_run(suite, mode)
            cancel = Event()
            future = self._executor.submit(self.runner.run, run_id, suite, mode, cancel)
            self._active = (run_id, cancel, future)
            future.add_done_callback(lambda _: self._release(run_id))
            return run_id

    def cancel(self, run_id: str) -> bool:
        with self._lock:
            if self._active is None or self._active[0] != run_id:
                return False
            self._active[1].set()
        return self.request_cancel(run_id) if self.request_cancel is not None else True

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def wait_for_idle(self, timeout: float) -> bool:
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            with self._lock:
                if self._active is None:
                    return True
            sleep(0.01)
        return False

    def _release(self, run_id: str) -> None:
        with self._lock:
            if self._active is not None and self._active[0] == run_id:
                self._active = None
