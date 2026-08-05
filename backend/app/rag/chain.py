import re
from collections.abc import Iterator
from typing import Protocol

from app.rag.conversation.rewriter import rewrite_standalone_question
from app.rag.conversation.summarizer import summarize_conversation
from app.rag.generation.answer_policy import NO_ANSWER_MESSAGE, is_missing_required_terms, is_no_answer, normalize_answer
from app.rag.generation.context_builder import build_context_blocks, format_context_blocks
from app.rag.retrieval.retriever import RetrievedChunk
from app.schemas.chat import ChatHistoryMessage, ChatResponse, SourceSnippet


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


# 将检索结果整理成 API 来源列表：同一 source_path 只展示一次，并按单来源和总量限制合并图片。
def _build_sources(
    retrieved: list[RetrievedChunk],
    max_images_per_source: int,
    max_images_per_answer: int,
) -> list[SourceSnippet]:
    sources_by_path: dict[str, SourceSnippet] = {}
    total_images = 0
    for index, item in enumerate(retrieved, start=1):
        evidence_id = f"资料 {index}"
        source_path = item.chunk.source_path
        existing = sources_by_path.get(source_path)
        if existing is None:
            remaining_images = max(max_images_per_answer - total_images, 0)
            images = list(item.chunk.images[: min(max_images_per_source, remaining_images)])
            total_images += len(images)
            sources_by_path[source_path] = SourceSnippet(
                title=item.chunk.title,
                source_path=source_path,
                snippet=item.chunk.content[:300],
                evidence_ids=[evidence_id],
                images=images,
                score=item.score,
                source_id=source_path,
                chunk_ids=[item.chunk.id],
            )
            continue

        if evidence_id not in existing.evidence_ids:
            existing.evidence_ids.append(evidence_id)
        if item.chunk.id not in existing.chunk_ids:
            existing.chunk_ids.append(item.chunk.id)
        for image in item.chunk.images:
            if total_images >= max_images_per_answer:
                break
            if len(existing.images) >= max_images_per_source:
                break
            if image not in existing.images:
                existing.images.append(image)
                total_images += 1
        if item.score is not None and (existing.score is None or item.score > existing.score):
            existing.score = item.score
    return list(sources_by_path.values())


# 将检索片段格式化为带标题和来源的证据块，帮助大模型理解每段资料的出处。
def _build_contexts(retrieved: list[RetrievedChunk]) -> list[str]:
    return format_context_blocks(build_context_blocks(retrieved))


# 确保有效回答至少带有资料编号引用，避免模型忘记按 prompt 输出引用。
def _ensure_answer_citations(answer: str, evidence_count: int) -> str:
    if evidence_count <= 0 or re.search(r"\[资料\s*\d+\]", answer):
        return answer

    references = "、".join(f"[资料 {index}]" for index in range(1, evidence_count + 1))
    return f"{answer}\n\n参考：{references}"


# 判断本轮是否需要更新摘要，用降频减少辅助模型调用。
def _should_update_conversation_summary(
    conversation_summary: str,
    conversation_turn_count: int,
    every_n_turns: int,
    has_conversation_context: bool,
    enabled: bool,
) -> bool:
    if not enabled or not has_conversation_context:
        return False
    if not conversation_summary.strip():
        return True
    if every_n_turns <= 1:
        return True
    return conversation_turn_count > 0 and conversation_turn_count % every_n_turns == 0


# 串联检索器和大模型，把用户问题转换成带来源的问答响应。
class RagChain:
    # 注入检索器和 LLM，便于测试时使用假对象，生产时使用真实服务。
    def __init__(
        self,
        retriever: RetrieverProtocol,
        llm: LLMProtocol,
        max_images_per_source: int = 5,
        max_images_per_answer: int = 8,
        enable_conversation_rewrite: bool = True,
        enable_conversation_summary: bool = True,
        conversation_summary_every_n_turns: int = 3,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.max_images_per_source = max_images_per_source
        self.max_images_per_answer = max_images_per_answer
        self.enable_conversation_rewrite = enable_conversation_rewrite
        self.enable_conversation_summary = enable_conversation_summary
        self.conversation_summary_every_n_turns = conversation_summary_every_n_turns

    # 执行完整 RAG 问答流程：处理连续对话、检索资料、生成回答、整理来源和图片。
    def answer(
        self,
        question: str,
        conversation_summary: str = "",
        conversation_turn_count: int = 0,
        recent_messages: list[ChatHistoryMessage] | None = None,
    ) -> ChatResponse:
        messages = recent_messages or []
        has_conversation_context = bool(conversation_summary.strip() or messages)
        standalone_question = rewrite_standalone_question(
            llm=self.llm,
            question=question,
            conversation_summary=conversation_summary,
            recent_messages=messages,
            enabled=self.enable_conversation_rewrite,
        )

        retrieved = self.retriever.retrieve(standalone_question)
        if not retrieved:
            return ChatResponse(
                answer=NO_ANSWER_MESSAGE,
                sources=[],
                conversation_summary=conversation_summary,
                standalone_question=standalone_question,
            )

        contexts = _build_contexts(retrieved)
        if is_missing_required_terms(question=standalone_question, contexts=contexts):
            return ChatResponse(
                answer=NO_ANSWER_MESSAGE,
                sources=[],
                conversation_summary=conversation_summary,
                standalone_question=standalone_question,
            )

        answer = normalize_answer(self.llm.generate(question=standalone_question, contexts=contexts))
        if is_no_answer(answer):
            return ChatResponse(
                answer=answer,
                sources=[],
                conversation_summary=conversation_summary,
                standalone_question=standalone_question,
            )

        answer = _ensure_answer_citations(answer, len(retrieved))
        should_update_summary = _should_update_conversation_summary(
            conversation_summary=conversation_summary,
            conversation_turn_count=conversation_turn_count,
            every_n_turns=self.conversation_summary_every_n_turns,
            has_conversation_context=has_conversation_context,
            enabled=self.enable_conversation_summary,
        )
        updated_summary = (
            summarize_conversation(
                llm=self.llm,
                previous_summary=conversation_summary,
                recent_messages=messages,
                question=question,
                answer=answer,
            )
            if should_update_summary
            else conversation_summary
        )
        return ChatResponse(
            answer=answer,
            sources=_build_sources(retrieved, self.max_images_per_source, self.max_images_per_answer),
            conversation_summary=updated_summary,
            standalone_question=standalone_question,
        )

    # 流式执行完整 RAG 问答流程：改写、检索、边生成边产出片段，最后返回来源和摘要。
    # 产出的事件为 dict，由路由层序列化为 SSE data 行，前端按 type 消费。
    def answer_stream(
        self,
        question: str,
        conversation_summary: str = "",
        conversation_turn_count: int = 0,
        recent_messages: list[ChatHistoryMessage] | None = None,
    ) -> Iterator[dict[str, object]]:
        messages = recent_messages or []
        has_conversation_context = bool(conversation_summary.strip() or messages)
        standalone_question = rewrite_standalone_question(
            llm=self.llm,
            question=question,
            conversation_summary=conversation_summary,
            recent_messages=messages,
            enabled=self.enable_conversation_rewrite,
        )

        retrieved = self.retriever.retrieve(standalone_question)
        if not retrieved:
            yield {"type": "answer", "content": NO_ANSWER_MESSAGE}
            yield {
                "type": "done",
                "conversation_summary": conversation_summary,
                "standalone_question": standalone_question,
            }
            return

        contexts = _build_contexts(retrieved)
        if is_missing_required_terms(question=standalone_question, contexts=contexts):
            yield {"type": "answer", "content": NO_ANSWER_MESSAGE}
            yield {
                "type": "done",
                "conversation_summary": conversation_summary,
                "standalone_question": standalone_question,
            }
            return

        # 边生成边推送回答片段；生成完成后统一做归一化、引用补全和摘要。
        streamed: list[str] = []
        for piece in self.llm.generate_stream(question=standalone_question, contexts=contexts):
            streamed.append(piece)
            yield {"type": "chunk", "content": piece}

        answer = normalize_answer("".join(streamed))
        if is_no_answer(answer):
            # 拒答文本已随 chunk 完整推送，无需再发 answer 事件。
            yield {
                "type": "done",
                "conversation_summary": conversation_summary,
                "standalone_question": standalone_question,
            }
            return

        answer = _ensure_answer_citations(answer, len(retrieved))
        should_update_summary = _should_update_conversation_summary(
            conversation_summary=conversation_summary,
            conversation_turn_count=conversation_turn_count,
            every_n_turns=self.conversation_summary_every_n_turns,
            has_conversation_context=has_conversation_context,
            enabled=self.enable_conversation_summary,
        )
        updated_summary = (
            summarize_conversation(
                llm=self.llm,
                previous_summary=conversation_summary,
                recent_messages=messages,
                question=question,
                answer=answer,
            )
            if should_update_summary
            else conversation_summary
        )
        yield {
            "type": "sources",
            "sources": [
                source.model_dump()
                for source in _build_sources(
                    retrieved, self.max_images_per_source, self.max_images_per_answer
                )
            ],
        }
        yield {
            "type": "done",
            "conversation_summary": updated_summary,
            "standalone_question": standalone_question,
        }
