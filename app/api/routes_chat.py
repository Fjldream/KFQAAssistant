from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key
from app.rag.factory import create_rag_chain
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])


# 问答接口：把 HTTP 请求交给 RAG Chain，并返回答案、来源和图片。
@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest):
    chain = create_rag_chain()
    return chain.answer(request.question)
