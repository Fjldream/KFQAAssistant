from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


# 问答接口的第一版连通性实现；任务 8 会接入真实 RAG Chain。
@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest):
    return ChatResponse(answer="问答路由已注册，当前返回固定状态用于接口连通性测试。", sources=[])
