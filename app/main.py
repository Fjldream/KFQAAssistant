from fastapi import FastAPI

from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_index import router as index_router
from app.core.logging import configure_logging


# 创建 FastAPI 应用并注册所有 API 路由，测试和生产启动都复用这一入口。
def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="KF RAG 问答助手", version="0.1.0")
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(index_router)
    return app


app = create_app()
