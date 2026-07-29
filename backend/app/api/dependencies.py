from fastapi import Header, HTTPException

from app.core.config import get_settings


# 校验内部 API Key；本地开发时可通过 DISABLE_AUTH=true 关闭。
def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if settings.disable_auth:
        return
    if not settings.app_api_key or x_api_key != settings.app_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
