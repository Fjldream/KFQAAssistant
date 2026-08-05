from fastapi.testclient import TestClient

from app.evaluation.coordinator import EvaluationRunConflict
from app.evaluation.models import (
    CaseResult,
    ComparisonResult,
    EvaluationCase,
    EvaluationRunDetail,
    EvaluationRunSummary,
    EvaluationTurn,
    GateResult,
    TurnResult,
)
from app.main import create_app


class FakeEvaluationService:
    def __init__(self) -> None:
        self.created: list[tuple[str, object]] = []
        self.approvals: list[dict] = []
        self.progressive_save_called = False
        self.runs = {
            "run-1": _detail("run-1", "completed"),
            "run-active": _detail("run-active", "running"),
            "run-invalid": _detail("run-invalid", "INVALID"),
        }

    def list_cases(self):
        return [
            EvaluationCase(
                id="single.collect.create",
                category="数采管理",
                priority="P0",
                tags=["smoke"],
                turns=[EvaluationTurn(question="如何创建采集工程？", expected_keywords=["新建工程"])],
            )
        ]

    def create_run(self, suite_id, mode):
        if suite_id == "busy":
            raise EvaluationRunConflict("an evaluation run is already active")
        if suite_id != "core":
            raise ValueError("unknown evaluation suite")
        self.created.append((suite_id, mode))
        self.runs["run-created"] = _detail("run-created", "created")
        return "run-created"

    def cancel_run(self, run_id: str):
        detail = self.runs.get(run_id)
        if detail is None or detail.summary.status in {"completed", "INVALID", "cancelled"}:
            return False
        self.runs[run_id] = _detail(run_id, "cancelled")
        return True

    def approve_baseline(self, run_id: str, approved_by: str, note: str | None = None):
        detail = self.runs.get(run_id)
        if detail is None:
            raise LookupError("run_not_found")
        if detail.summary.status == "INVALID":
            raise ValueError("run_invalid")
        if detail.summary.status != "completed":
            raise RuntimeError("run_not_terminal")
        approval = {"suite_id": "core", "run_id": run_id, "approved_by": approved_by, "note": note}
        self.approvals.append(approval)
        return approval

    def list_baselines(self):
        return self.approvals

    def compare_to_baseline(self, run_id: str, baseline_run_id: str | None = None):
        if run_id not in self.runs:
            raise LookupError("run_not_found")
        if not self.approvals:
            return None
        return ComparisonResult(pass_rate_delta=0.1, recovered_case_ids=["case-1"])

    def list_runs(self, limit=20):
        return [detail.summary for detail in self.runs.values()][:limit]

    def get_run(self, run_id: str):
        return self.runs.get(run_id)

    def get_overview(self):
        return {"latest": self.runs["run-1"], "previous_run_id": None, "comparison": None}

    def save_case_results(self, *args, **kwargs):
        self.progressive_save_called = True
        raise AssertionError("progressive uploads must never save client scores")


def _summary(run_id: str, status: str) -> EvaluationRunSummary:
    return EvaluationRunSummary(
        run_id=run_id,
        status=status,
        case_total=1,
        case_passed=1,
        pass_rate=1.0,
        p0_total=1,
        p0_passed=1,
    )


def _detail(run_id: str, status: str) -> EvaluationRunDetail:
    turn = TurnResult(
        question="如何创建采集工程？",
        answer="点击新建工程。",
        standalone_question="如何创建采集工程？",
        passed=True,
        keyword_passed=True,
        source_passed=True,
        image_passed=True,
        no_answer_passed=True,
    )
    case = CaseResult(
        case_id="single.collect.create",
        category="数采管理",
        priority="P0",
        case_type="single",
        passed=True,
        turn_results=[turn],
    )
    return EvaluationRunDetail(summary=_summary(run_id, status), gate_result=GateResult(passed=True), case_results=[case])


def _client(monkeypatch):
    from app.api import routes_evaluation

    service = FakeEvaluationService()
    monkeypatch.setattr(routes_evaluation, "create_evaluation_service", lambda: service)
    return TestClient(create_app()), service


def test_evaluation_cases_endpoint(monkeypatch):
    client, _ = _client(monkeypatch)

    response = client.get("/api/evaluation/cases")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "single.collect.create"
    assert response.json()[0]["case_type"] == "single"


def test_create_run_returns_202_and_does_not_accept_case_results(monkeypatch):
    client, service = _client(monkeypatch)

    response = client.post("/api/evaluation/runs", json={"suite_id": "core", "mode": "calibration"})

    assert response.status_code == 202
    assert response.json()["run_id"] == "run-created"
    assert response.json()["status"] in {"created", "running"}
    assert service.created[0][0] == "core"

    rejected = client.post(
        "/api/evaluation/runs",
        json={"suite_id": "core", "mode": "calibration", "case_results": []},
    )
    assert rejected.status_code == 422


def test_create_run_returns_stable_conflict(monkeypatch):
    client, _ = _client(monkeypatch)

    response = client.post("/api/evaluation/runs", json={"suite_id": "busy", "mode": "blocking"})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "run_conflict"


def test_cancel_run_returns_updated_summary(monkeypatch):
    client, _ = _client(monkeypatch)

    response = client.post("/api/evaluation/runs/run-active/cancel")

    assert response.status_code == 200
    assert response.json()["run_id"] == "run-active"
    assert response.json()["status"] == "cancelled"


def test_run_detail_missing_run_returns_stable_error(monkeypatch):
    client, _ = _client(monkeypatch)

    response = client.get("/api/evaluation/runs/missing")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"


def test_cancel_terminal_run_returns_stable_error(monkeypatch):
    client, _ = _client(monkeypatch)

    response = client.post("/api/evaluation/runs/run-1/cancel")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "run_not_terminal"


def test_approve_baseline_validates_approver_and_invalid_run(monkeypatch):
    client, _ = _client(monkeypatch)

    blank_approver = client.post("/api/evaluation/runs/run-1/approve-baseline", json={"approved_by": "   "})
    invalid_run = client.post("/api/evaluation/runs/run-invalid/approve-baseline", json={"approved_by": "release"})

    assert blank_approver.status_code == 422
    assert invalid_run.status_code == 422
    assert invalid_run.json()["detail"]["code"] == "run_invalid"


def test_approve_baseline_persists_note_and_lists_immutable_approvals(monkeypatch):
    client, service = _client(monkeypatch)

    approval = client.post(
        "/api/evaluation/runs/run-1/approve-baseline",
        json={"approved_by": "  release manager  ", "note": "known-good release"},
    )
    baselines = client.get("/api/evaluation/baselines")

    assert approval.status_code == 200
    assert approval.json()["approved_by"] == "release manager"
    assert approval.json()["note"] == "known-good release"
    assert baselines.status_code == 200
    assert baselines.json() == [approval.json()]
    assert service.approvals[0]["note"] == "known-good release"


def test_comparison_uses_approved_suite_baseline(monkeypatch):
    client, _ = _client(monkeypatch)
    client.post("/api/evaluation/runs/run-1/approve-baseline", json={"approved_by": "release"})

    response = client.get("/api/evaluation/runs/run-active/compare")

    assert response.status_code == 200
    assert response.json()["recovered_case_ids"] == ["case-1"]


def test_progressive_upload_is_gone_and_never_saves_client_scores(monkeypatch):
    client, service = _client(monkeypatch)

    response = client.post("/api/evaluation/runs/progressive", json={"case_results": [], "config": {}})

    assert response.status_code == 410
    assert response.json()["detail"]["code"] == "progressive_run_deprecated"
    assert service.progressive_save_called is False


def test_run_list_limit_is_bounded(monkeypatch):
    client, _ = _client(monkeypatch)

    response = client.get("/api/evaluation/runs?limit=101")

    assert response.status_code == 422
