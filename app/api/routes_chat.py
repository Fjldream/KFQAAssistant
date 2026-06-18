import logging
from time import perf_counter

from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key
from app.rag.factory import create_rag_chain
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


# 统计一次回答返回的图片总数，用于日志和线上排查。
def _image_count(response: ChatResponse) -> int:
    return sum(len(source.images) for source in response.sources)


# 记录一次成功问答的关键指标，不记录原始问题内容，降低日志敏感信息风险。
def _log_chat_completed(question: str, response: ChatResponse, elapsed_ms: int) -> None:
    logger.info(
        "chat_completed question_length=%s source_count=%s image_count=%s elapsed_ms=%s",
        len(question),
        len(response.sources),
        _image_count(response),
        elapsed_ms,
    )


# 问答接口：把 HTTP 请求交给 RAG Chain，并返回答案、来源和图片。
@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest) -> ChatResponse:
    started_at = perf_counter()
    chain = create_rag_chain()
    try:
        response = chain.answer(request.question)
    except Exception:
        elapsed_ms = int((perf_counter() - started_at) * 1000)
        logger.exception("chat_failed question_length=%s elapsed_ms=%s", len(request.question), elapsed_ms)
        raise

    elapsed_ms = int((perf_counter() - started_at) * 1000)
    _log_chat_completed(request.question, response, elapsed_ms)
    return response
