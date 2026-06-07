from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key

router = APIRouter(prefix="/api/index", tags=["index"])


# 索引重建接口的第一版连通性实现；任务 8 会接入真实索引构建流程。
@router.post("/rebuild", dependencies=[Depends(verify_api_key)])
def rebuild_index():
    return {"status": "accepted", "message": "索引路由已注册，当前返回固定状态用于接口连通性测试。"}
