from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import verify_api_key
from app.evaluation.models import EvaluationCase
from app.evaluation.schemas import CreateEvaluationRunRequest, RunEvaluationCaseRequest, SaveProgressiveRunRequest
from app.evaluation.service import create_evaluation_service
from app.rag.errors import RagServiceError

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"], dependencies=[Depends(verify_api_key)])


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
def evaluation_overview():
    return create_evaluation_service().get_overview()


# 获取当前评测用例列表，前端 v1 只读展示。
@router.get("/cases")
def evaluation_cases():
    return [_case_to_response(case) for case in create_evaluation_service().list_cases()]


# 同步创建一次评测运行，并返回完整评测报告。
@router.post("/runs")
def create_evaluation_run(request: CreateEvaluationRunRequest):
    try:
        return create_evaluation_service().run_evaluation(
            include_dialogues=request.include_dialogues,
            include_load_test=request.include_load_test,
        )
    except RagServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc


# 运行单条评测用例，前端用它逐条展示进度。
@router.post("/cases/{case_id}/run")
def run_evaluation_case(case_id: str, request: RunEvaluationCaseRequest):
    try:
        result = create_evaluation_service().run_case(
            case_id=case_id,
            include_dialogues=request.include_dialogues,
        )
    except RagServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="评测用例不存在")
    return result


# 保存前端逐条运行得到的评测结果，形成可查询的历史报告。
@router.post("/runs/progressive")
def save_progressive_evaluation_run(request: SaveProgressiveRunRequest):
    service = create_evaluation_service()
    case_results = [service.case_result_from_payload(result.model_dump()) for result in request.case_results]
    return service.save_case_results(
        case_results,
        config={**request.config, "mode": "progressive"},
    )


# 获取最近评测运行列表。
@router.get("/runs")
def evaluation_runs(limit: int = 20):
    return create_evaluation_service().list_runs(limit=limit)


# 获取某次评测运行的完整详情。
@router.get("/runs/{run_id}")
def evaluation_run_detail(run_id: str):
    detail = create_evaluation_service().get_run(run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="评测运行不存在")
    return detail


# 获取某次评测运行相对基准运行的对比结果。
@router.get("/runs/{run_id}/compare")
def evaluation_run_comparison(run_id: str, baseline_run_id: str | None = None):
    comparison = create_evaluation_service().compare_run(run_id=run_id, baseline_run_id=baseline_run_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail="缺少可对比的评测运行")
    return comparison
