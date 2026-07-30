from dataclasses import dataclass
from typing import Protocol

from app.rag.errors import IndexNotReadyError
from app.rag.models import DocumentChunk
from app.rag.retrieval.query_rewriter import QueryRewriterProtocol


# 表示一次检索命中的 chunk，同时带有向量库返回的相关性分数。
@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float | None = None


# 定义向量库需要提供的最小检索接口，便于以后替换 Chroma、Milvus 或 Qdrant。
class VectorStoreProtocol(Protocol):
    # 返回当前向量库中的 chunk 数量，用于判断索引是否已经构建。
    def count(self) -> int:
        ...

    # 根据用户问题检索最相关的 top_k 个知识片段。
    def similarity_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        ...


# 定义重排序器接口，便于用规则重排、模型重排或测试假对象替换。
class RerankerProtocol(Protocol):
    # 根据用户问题对候选资料重新排序，并截断到指定数量。
    def __call__(self, query: str, candidates: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
        ...


# RAG 检索服务：屏蔽具体向量库细节，对外只暴露 retrieve 方法。
class RetrieverService:
    # 注入向量库、top_k、可选查询改写器和重排序器，方便测试时替换成假对象。
    def __init__(
        self,
        vector_store: VectorStoreProtocol,
        top_k: int = 5,
        query_rewriter: QueryRewriterProtocol | None = None,
        candidate_limit: int = 50,
        reranker: RerankerProtocol | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.top_k = top_k
        self.query_rewriter = query_rewriter
        self.candidate_limit = candidate_limit
        self.reranker = reranker

    # 根据用户问题调用向量库检索，返回带来源信息的相关 chunks。
    def retrieve(self, query: str) -> list[RetrievedChunk]:
        if self.vector_store.count() <= 0:
            raise IndexNotReadyError()
        if self.query_rewriter is None:
            return self._rerank(query, self.vector_store.similarity_search(query, self.top_k))

        from app.rag.retrieval.multi_query import merge_retrieved_candidates

        rewrite_result = self.query_rewriter.rewrite(query)
        results_by_query = {
            rewritten_query: self.vector_store.similarity_search(rewritten_query, self.top_k)
            for rewritten_query in rewrite_result.queries
        }
        candidates = merge_retrieved_candidates(results_by_query, self.candidate_limit)
        return self._rerank(query, candidates)

    # 对检索候选执行可选重排，没有配置重排器时保留原始顺序并截断。
    def _rerank(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if self.reranker is None:
            return candidates[: self.top_k]
        return self.reranker(query, candidates, self.top_k)
