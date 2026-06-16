from typing import Protocol

from app.rag.answer_policy import NO_ANSWER_MESSAGE, is_missing_required_terms, is_no_answer, normalize_answer
from app.rag.retriever import RetrievedChunk
from app.schemas.chat import ChatResponse, SourceSnippet


# 定义 RAG Chain 需要的检索器接口，让 Chain 不依赖具体向量库实现。
class RetrieverProtocol(Protocol):
    # 根据用户问题返回相关手册片段。
    def retrieve(self, query: str) -> list[RetrievedChunk]:
        ...


# 定义 RAG Chain 需要的 LLM 接口，让 Chain 不依赖具体模型供应商。
class LLMProtocol(Protocol):
    # 根据用户问题和检索上下文生成最终回答。
    def generate(self, question: str, contexts: list[str]) -> str:
        ...


# 串联检索器和大模型，把用户问题转换成带来源的问答响应。
class RagChain:
    # 注入检索器和 LLM，便于测试时使用假对象，生产时使用真实服务。
    def __init__(self, retriever: RetrieverProtocol, llm: LLMProtocol) -> None:
        self.retriever = retriever
        self.llm = llm

    # 执行完整 RAG 问答流程：检索资料、生成回答、整理来源和图片。
    def answer(self, question: str) -> ChatResponse:
        retrieved = self.retriever.retrieve(question)
        if not retrieved:
            return ChatResponse(answer=NO_ANSWER_MESSAGE, sources=[])

        contexts = [item.chunk.content for item in retrieved]
        if is_missing_required_terms(question=question, contexts=contexts):
            return ChatResponse(answer=NO_ANSWER_MESSAGE, sources=[])

        answer = normalize_answer(self.llm.generate(question=question, contexts=contexts))
        if is_no_answer(answer):
            return ChatResponse(answer=answer, sources=[])

        sources = [
            SourceSnippet(
                title=item.chunk.title,
                source_path=item.chunk.source_path,
                snippet=item.chunk.content[:300],
                images=item.chunk.images,
                score=item.score,
            )
            for item in retrieved
        ]
        return ChatResponse(answer=answer, sources=sources)
