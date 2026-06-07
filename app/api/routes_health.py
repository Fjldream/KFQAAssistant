from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


# 健康检查接口，用于确认服务进程和路由系统可用。
@router.get("/health")
def health():
    return {"status": "ok"}
