from dataclasses import asdict

from fastapi.testclient import TestClient

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
from app.rag.errors import LLMGenerationError


class FakeEvaluationService:
    # 返回固定用例列表，验证 API 层只做 HTTP 转换。
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

    # 返回固定运行详情，验证创建评测接口的响应结构。
    def run_evaluation(self, include_dialogues=True, include_load_test=False):
        return _detail(run_id="run-1")

    # 返回单条用例评测结果，验证前端逐条评测接口。
    def run_case(self, case_id: str, include_dialogues=True):
        assert case_id == "single.collect.create"
        return _detail(run_id="run-1").case_results[0]

    # 保存前端逐条评测完成后的结果，验证渐进式评测收口。
    def save_case_results(self, case_results, config=None):
        assert len(case_results) == 1
        return _detail(run_id="run-progressive")

    # 测试假服务直接复用传入 payload，不关心转换细节。
    def case_result_from_payload(self, payload):
        return payload

    # 返回固定运行列表，验证列表接口。
    def list_runs(self, limit=20):
        return [_summary("run-1")]

    # 返回固定运行详情，验证详情接口。
    def get_run(self, run_id: str):
        return _detail(run_id=run_id)

    # 返回固定总览，验证总览接口。
    def get_overview(self):
        return {"latest": _detail("run-1"), "previous_run_id": None, "comparison": None}

    # 返回固定对比结果，验证对比接口。
    def compare_run(self, run_id: str, baseline_run_id=None):
        return ComparisonResult(pass_rate_delta=0.1, recovered_case_ids=["case-1"])


class FailingEvaluationService(FakeEvaluationService):
    # 模拟模型服务不可用，验证评测路由不会把业务异常暴露成 500。
    def run_evaluation(self, include_dialogues=True, include_load_test=False):
        raise LLMGenerationError()


# 构造运行汇总，供假服务复用。
def _summary(run_id: str) -> EvaluationRunSummary:
    return EvaluationRunSummary(
        run_id=run_id,
        status="completed",
        case_total=1,
        case_passed=1,
        pass_rate=1.0,
        p0_total=1,
        p0_passed=1,
    )


# 构造完整运行详情，供假服务复用。
def _detail(run_id: str) -> EvaluationRunDetail:
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
    return EvaluationRunDetail(summary=_summary(run_id), gate_result=GateResult(passed=True), case_results=[case])


# 构造带假评测服务的测试客户端。
def _client(monkeypatch):
    from app.api import routes_evaluation

    monkeypatch.setattr(routes_evaluation, "create_evaluation_service", lambda: FakeEvaluationService())
    return TestClient(create_app())


# 构造会在创建评测时失败的测试客户端。
def _failing_client(monkeypatch):
    from app.api import routes_evaluation

    monkeypatch.setattr(routes_evaluation, "create_evaluation_service", lambda: FailingEvaluationService())
    return TestClient(create_app())


# 验证用例列表接口返回前端需要的统一结构。
def test_evaluation_cases_endpoint(monkeypatch):
    client = _client(monkeypatch)

    response = client.get("/api/evaluation/cases")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "single.collect.create"
    assert response.json()[0]["case_type"] == "single"


# 验证创建评测运行接口返回完整报告。
def test_evaluation_create_run_endpoint(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/evaluation/runs", json={"include_dialogues": True, "include_load_test": False})

    assert response.status_code == 200
    assert response.json()["summary"]["run_id"] == "run-1"
    assert response.json()["gate_result"]["passed"] is True


# 验证单条用例运行接口返回用例结果。
def test_evaluation_run_single_case_endpoint(monkeypatch):
    client = _client(monkeypatch)

    response = client.post("/api/evaluation/cases/single.collect.create/run", json={"include_dialogues": True})

    assert response.status_code == 200
    assert response.json()["case_id"] == "single.collect.create"


# 验证保存渐进式评测结果接口返回完整运行报告。
def test_evaluation_save_progressive_run_endpoint(monkeypatch):
    client = _client(monkeypatch)
    case_payload = asdict(_detail("run-1").case_results[0])

    response = client.post(
        "/api/evaluation/runs/progressive",
        json={"case_results": [case_payload], "config": {"mode": "progressive"}},
    )

    assert response.status_code == 200
    assert response.json()["summary"]["run_id"] == "run-progressive"


# 验证模型服务不可用时，评测接口返回用户可读错误而不是 500。
def test_evaluation_create_run_returns_service_error(monkeypatch):
    client = _failing_client(monkeypatch)

    response = client.post("/api/evaluation/runs", json={"include_dialogues": True, "include_load_test": False})

    assert response.status_code == 503
    assert response.json()["detail"] == "大模型服务暂时不可用，请稍后重试。"


# 验证运行详情和对比接口可访问。
def test_evaluation_detail_and_compare_endpoints(monkeypatch):
    client = _client(monkeypatch)

    detail = client.get("/api/evaluation/runs/run-1")
    comparison = client.get("/api/evaluation/runs/run-1/compare")

    assert detail.status_code == 200
    assert detail.json()["case_results"][0]["case_id"] == "single.collect.create"
    assert comparison.status_code == 200
    assert comparison.json()["recovered_case_ids"] == ["case-1"]
