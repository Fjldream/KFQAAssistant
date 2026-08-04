from functools import lru_cache

from app.core.config import get_settings
from app.rag.chain import RagChain
from app.rag.retrieval.embeddings import LazyEmbeddings
from app.rag.generation.llm import DeepSeekClient
from app.rag.retrieval.query_rewriter import DeepSeekQueryRewriter
from app.rag.retrieval.reranker import rerank
from app.rag.retrieval.retriever import RetrieverService
from app.rag.retrieval.vector_store import ChromaVectorStore


# 创建真实 Chroma 向量库实例，集中管理 embedding 和持久化目录配置。
@lru_cache(maxsize=1)
def create_vector_store() -> ChromaVectorStore:
    settings = get_settings()
    embeddings = LazyEmbeddings(settings.embedding_model_name)
    return ChromaVectorStore(
        settings.chroma_persist_dir,
        embeddings,
        max_chunks_per_source=settings.retrieval_max_chunks_per_source,
    )


# 创建生产用 RAG Chain，把向量检索、Retriever 和 DeepSeek 客户端组装起来。
@lru_cache(maxsize=1)
def create_rag_chain() -> RagChain:
    settings = get_settings()
    vector_store = create_vector_store()
    query_rewriter = (
        DeepSeekQueryRewriter(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=settings.deepseek_timeout_seconds,
            max_queries=settings.query_rewrite_max_queries,
        )
        if settings.enable_query_rewrite
        else None
    )
    retriever = RetrieverService(
        vector_store=vector_store,
        top_k=settings.top_k,
        query_rewriter=query_rewriter,
        candidate_limit=settings.multi_query_candidate_limit,
        reranker=rerank,
    )
    llm = DeepSeekClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
    )
    return RagChain(
        retriever=retriever,
        llm=llm,
        max_images_per_source=settings.max_images_per_source,
        max_images_per_answer=settings.max_images_per_answer,
        enable_conversation_rewrite=settings.enable_conversation_rewrite,
        enable_conversation_summary=settings.enable_conversation_summary,
        conversation_summary_every_n_turns=settings.conversation_summary_every_n_turns,
    )


# 清理 RAG 工厂缓存，用于索引重建后让后续请求重新获取最新向量库对象。
def clear_rag_factory_cache() -> None:
    create_rag_chain.cache_clear()
    create_vector_store.cache_clear()
