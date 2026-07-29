from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_index import router as index_router
from app.core.config import get_settings
from app.core.logging import configure_logging


# 从逗号分隔配置中解析允许访问 API 的前端来源。
def _parse_cors_origins(raw_origins: str) -> list[str]:
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


# 配置浏览器跨域访问，让本地 Vue 前端和后续企业前端域名可以调用 API。
def _configure_cors(app: FastAPI) -> None:
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(settings.cors_allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# 挂载手册静态资源，让前端可以预览 RAG 返回的相对图片路径。
def _mount_manual_static_files(app: FastAPI) -> None:
    settings = get_settings()
    app.mount("/manuals", StaticFiles(directory=settings.data_dir, check_dir=False), name="manuals")


# 创建 FastAPI 应用并注册所有 API 路由，测试和生产启动都复用这一入口。
def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="KF RAG 问答助手", version="0.1.0")
    _configure_cors(app)
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(index_router)
    _mount_manual_static_files(app)
    return app


app = create_app()
