from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import verify_api_key
from app.evaluation.coordinator import EvaluationRunConflict
from app.evaluation.models import EvaluationCase, GateMode
from app.evaluation.schemas import (
    ApproveBaselineRequest,
    BaselineApprovalResponse,
    CreateEvaluationRunRequest,
    EvaluationRunSummaryResponse,
    RunEvaluationCaseRequest,
)
from app.evaluation.service import EvaluationService
from app.rag.errors import RagServiceError

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"], dependencies=[Depends(verify_api_key)])


def get_evaluation_service(request: Request) -> EvaluationService:
    return request.app.state.evaluation_service


def _api_error(status_code: int, code: str, message: str) -> NoReturn:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _raise_service_error(exc: Exception) -> NoReturn:
    code = str(exc)
    if code == "run_not_found":
        _api_error(404, code, "评测运行不存在")
    if code == "run_not_terminal":
        _api_error(409, code, "评测运行已结束，不能执行该操作")
    if code in {"run_invalid", "suite_mismatch"}:
        _api_error(422, code, "评测运行不满足该操作的条件")
    _api_error(422, "run_invalid", "评测运行请求无效")


# 把领域用例转换成 API 展示结构，补充 dataclass property 不会自动序列化的 case_type。
def _case_to_response(case: EvaluationCase) -> dict:
    return {
        "id": case.id,
        "category": case.category,
        "priority": case.priority,
        "tags": case.tags,
        "case_type": case.case_type,
        "turns": [
            {
                "question": turn.question,
                "expected_keywords": turn.expected_keywords,
                "expected_keyword_groups": turn.expected_keyword_groups,
                "expected_source_keywords": turn.expected_source_keywords,
                "expected_source_keyword_groups": turn.expected_source_keyword_groups,
                "forbidden_source_keywords": turn.forbidden_source_keywords,
                "expect_images": turn.expect_images,
                "expect_no_answer": turn.expect_no_answer,
                "min_sources": turn.min_sources,
                "min_images": turn.min_images,
            }
            for turn in case.turns
        ],
    }


# 获取评测中心总览，包含最近一次运行、上一轮运行和对比摘要。
@router.get("/overview")
def evaluation_overview(service: EvaluationService = Depends(get_evaluation_service)):
    return service.get_overview()


# 获取当前评测用例列表，前端 v1 只读展示。
@router.get("/cases")
def evaluation_cases(service: EvaluationService = Depends(get_evaluation_service)):
    return [_case_to_response(case) for case in service.list_cases()]


# 创建由后端执行的异步评测运行，只返回可轮询的运行汇总。
@router.post("/runs", response_model=EvaluationRunSummaryResponse, status_code=status.HTTP_202_ACCEPTED)
def create_evaluation_run(request: CreateEvaluationRunRequest, service: EvaluationService = Depends(get_evaluation_service)):
    try:
        run_id = service.create_run(request.suite_id, GateMode(request.mode.value.upper()))
    except EvaluationRunConflict as exc:
        _api_error(409, "run_conflict", "已有评测运行正在执行")
    except ValueError as exc:
        _raise_service_error(exc)
    detail = service.get_run(run_id)
    if detail is None:
        _api_error(404, "run_not_found", "评测运行不存在")
    return detail.summary


# 运行单条评测用例，前端用它逐条展示进度。
@router.post("/cases/{case_id}/run")
def run_evaluation_case(case_id: str, request: RunEvaluationCaseRequest, service: EvaluationService = Depends(get_evaluation_service)):
    try:
        result = service.run_case(
            case_id=case_id,
            include_dialogues=request.include_dialogues,
        )
    except RagServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="评测用例不存在")
    return result


# 兼容期保留端点，但拒绝浏览器提交评分结果。
@router.post("/runs/progressive")
def save_progressive_evaluation_run():
    _api_error(410, "progressive_run_deprecated", "请使用 POST /api/evaluation/runs 创建后端执行的评测运行")


# 获取最近评测运行列表。
@router.get("/runs")
def evaluation_runs(limit: int = Query(default=20, ge=1, le=100), service: EvaluationService = Depends(get_evaluation_service)):
    return service.list_runs(limit=limit)


# 获取某次评测运行的完整详情。
@router.get("/runs/{run_id}")
def evaluation_run_detail(run_id: str, service: EvaluationService = Depends(get_evaluation_service)):
    detail = service.get_run(run_id)
    if detail is None:
        _api_error(404, "run_not_found", "评测运行不存在")
    return detail


# 取消仍在运行的评测，并返回持久化的最新摘要。
@router.post("/runs/{run_id}/cancel", response_model=EvaluationRunSummaryResponse)
def cancel_evaluation_run(run_id: str, service: EvaluationService = Depends(get_evaluation_service)):
    detail = service.get_run(run_id)
    if detail is None:
        _api_error(404, "run_not_found", "评测运行不存在")
    if str(detail.summary.status) in {"completed", "INVALID", "cancelled"}:
        _api_error(409, "run_not_terminal", "评测运行已结束，不能取消")
    if not service.cancel_run(run_id):
        _api_error(409, "run_not_terminal", "评测运行已结束，不能取消")
    updated = service.get_run(run_id)
    if updated is None:
        _api_error(404, "run_not_found", "评测运行不存在")
    return updated.summary


@router.post("/runs/{run_id}/approve-baseline", response_model=BaselineApprovalResponse)
def approve_evaluation_baseline(run_id: str, request: ApproveBaselineRequest, service: EvaluationService = Depends(get_evaluation_service)):
    try:
        return service.approve_baseline(run_id, request.approved_by, request.note)
    except (LookupError, RuntimeError, ValueError) as exc:
        _raise_service_error(exc)


@router.get("/baselines", response_model=list[BaselineApprovalResponse])
def evaluation_baselines(service: EvaluationService = Depends(get_evaluation_service)):
    return service.list_baselines()


# 获取某次评测运行相对同 Suite 已批准基准的对比结果。
@router.get("/runs/{run_id}/compare")
def evaluation_run_comparison(run_id: str, baseline_run_id: str | None = None, service: EvaluationService = Depends(get_evaluation_service)):
    try:
        comparison = service.compare_to_baseline(run_id, baseline_run_id)
    except (LookupError, ValueError) as exc:
        _raise_service_error(exc)
    if comparison is None:
        _api_error(422, "run_invalid", "当前 Suite 没有已批准的基准运行")
    return comparison
