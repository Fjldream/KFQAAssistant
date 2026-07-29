from dataclasses import dataclass
from typing import Protocol

from app.rag.errors import IndexNotReadyError
from app.rag.models import DocumentChunk


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


# RAG 检索服务：屏蔽具体向量库细节，对外只暴露 retrieve 方法。
class RetrieverService:
    # 注入向量库和 top_k 参数，方便测试时替换成假向量库。
    def __init__(self, vector_store: VectorStoreProtocol, top_k: int = 5) -> None:
        self.vector_store = vector_store
        self.top_k = top_k

    # 根据用户问题调用向量库检索，返回带来源信息的相关 chunks。
    def retrieve(self, query: str) -> list[RetrievedChunk]:
        if self.vector_store.count() <= 0:
            raise IndexNotReadyError()
        return self.vector_store.similarity_search(query, self.top_k)
