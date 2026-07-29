import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.rag.factory import create_vector_store

router = APIRouter(prefix="/api", tags=["health"])
logger = logging.getLogger(__name__)


# 健康检查接口，用于确认服务进程和路由系统可用。
@router.get("/health")
def health():
    return {"status": "ok"}


# 判断当前环境是否属于生产类环境，用于启用更严格的配置检查。
def _is_production_env(app_env: str) -> bool:
    return app_env.strip().lower() not in {"", "local", "dev", "development", "test"}


# 检查 DeepSeek API Key 是否配置，缺失时问答接口无法调用大模型。
def _check_deepseek_api_key(settings, checks: dict[str, str], issues: list[str]) -> None:
    if settings.deepseek_api_key.strip():
        checks["deepseek_api_key"] = "ok"
        return

    checks["deepseek_api_key"] = "error"
    issues.append("未配置 DEEPSEEK_API_KEY，问答接口无法调用大模型。")


# 检查认证配置是否安全，避免生产环境误开免认证访问。
def _check_auth(settings, checks: dict[str, str], issues: list[str]) -> None:
    if _is_production_env(settings.app_env) and settings.disable_auth:
        checks["auth"] = "error"
        issues.append("生产环境不能关闭 API Key 认证，请设置 DISABLE_AUTH=false 并配置 APP_API_KEY。")
        return

    if not settings.disable_auth and not settings.app_api_key.strip():
        checks["auth"] = "error"
        issues.append("已开启 API Key 认证，但未配置 APP_API_KEY。")
        return

    checks["auth"] = "ok"


# 检查向量库是否已经构建，返回当前索引中的 chunk 数量。
def _check_index(checks: dict[str, str], issues: list[str]) -> int:
    try:
        chunks = create_vector_store().count()
    except Exception:
        logger.exception("readiness_index_check_failed")
        checks["index"] = "error"
        issues.append("知识库索引检查失败，请查看服务日志。")
        return 0

    if chunks <= 0:
        checks["index"] = "error"
        issues.append("知识库索引为空，请先执行索引构建。")
        return chunks

    checks["index"] = "ok"
    return chunks


# 服务就绪检查接口，用于部署平台判断问答服务是否可以真正接收流量。
@router.get("/health/ready")
def readiness():
    settings = get_settings()
    checks: dict[str, str] = {}
    issues: list[str] = []

    _check_deepseek_api_key(settings, checks, issues)
    _check_auth(settings, checks, issues)
    chunks = _check_index(checks, issues)

    status = "ready" if not issues else "not_ready"
    payload = {
        "status": status,
        "checks": checks,
        "issues": issues,
        "chunks": chunks,
    }
    return JSONResponse(status_code=200 if status == "ready" else 503, content=payload)
