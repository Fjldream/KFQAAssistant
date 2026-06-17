from pathlib import Path
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk


# 从中文问题中扩展关键词，补足“操作系统”等问法和手册里的“系统环境/软件要求”之间的表达差异。
def expand_query_terms(query: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9_.+-]+|[\u4e00-\u9fff]+", query)
    expanded: list[str] = []
    for term in terms:
        expanded.append(term)
        if re.fullmatch(r"[\u4e00-\u9fff]+", term) and len(term) > 1:
            expanded.extend(term[index : index + 2] for index in range(len(term) - 1))
    if "操作系统" in query:
        expanded.extend(["系统环境", "软件要求", "Windows", "Linux", "Chrome"])
    return list(dict.fromkeys(item for item in expanded if len(item) >= 2))


# 计算 query 和 chunk 的关键词匹配分，用来弥补纯向量检索在产品术语上的偏差。
def keyword_score(query: str, chunk: DocumentChunk) -> float:
    terms = expand_query_terms(query)
    title_source = f"{chunk.title}\n{chunk.source_path}"
    text = f"{title_source}\n{chunk.content}"
    score = 0.0
    for term in terms:
        if term in title_source:
            score += 3.0
        if term in chunk.content:
            score += 1.0
    return score


# 对已排序的检索结果做来源多样性筛选，优先覆盖更多不同 source_path。
def diversify_results(results: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    selected: list[RetrievedChunk] = []
    selected_ids: set[str] = set()
    used_sources: set[str] = set()

    for item in results:
        if item.chunk.source_path in used_sources:
            continue
        selected.append(item)
        selected_ids.add(item.chunk.id)
        used_sources.add(item.chunk.source_path)
        if len(selected) == top_k:
            return selected

    for item in results:
        if item.chunk.id in selected_ids:
            continue
        selected.append(item)
        if len(selected) == top_k:
            return selected

    return selected


# Chroma 向量库封装，负责写入 chunks 和执行相似度检索。
class ChromaVectorStore:
    # 初始化 Chroma collection，并绑定 embedding 函数和持久化目录。
    def __init__(self, persist_dir: Path, embeddings) -> None:
        self.persist_dir = persist_dir
        self.embeddings = embeddings
        self.store = Chroma(
            collection_name="kf_manual",
            persist_directory=str(persist_dir),
            embedding_function=embeddings,
        )

    # 将切好的 chunks 写入 Chroma，返回写入数量，供索引构建脚本展示进度。
    def rebuild(self, chunks: list[DocumentChunk]) -> int:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.store.reset_collection()
        ids = [chunk.id for chunk in chunks]
        documents = [
            Document(
                page_content=chunk.content,
                metadata={
                    "id": chunk.id,
                    "title": chunk.title,
                    "source_path": chunk.source_path,
                    "images": "|".join(chunk.images),
                },
            )
            for chunk in chunks
        ]
        if ids:
            self.store.add_documents(documents=documents, ids=ids)
        return len(ids)

    # 根据用户问题检索相关 chunks，并把 Chroma 结果还原成业务层 RetrievedChunk。
    def similarity_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        vector_results = self.store.similarity_search_with_relevance_scores(query, k=max(top_k * 4, top_k))
        candidates: dict[str, RetrievedChunk] = {}
        for document, score in vector_results:
            chunk = self._document_to_chunk(document)
            candidates[chunk.id] = RetrievedChunk(chunk=chunk, score=float(score))

        for chunk in self._keyword_candidates(query, limit=top_k * 4):
            candidates.setdefault(chunk.id, RetrievedChunk(chunk=chunk, score=0.0))

        ranked = sorted(
            candidates.values(),
            key=lambda item: (item.score or 0.0) + keyword_score(query, item.chunk) * 0.08,
            reverse=True,
        )
        return diversify_results(ranked, top_k)

    # 将 LangChain Document 还原为业务层 DocumentChunk。
    def _document_to_chunk(self, document: Document) -> DocumentChunk:
        images = document.metadata.get("images", "")
        return DocumentChunk(
            id=str(document.metadata.get("id", "")),
            title=str(document.metadata.get("title", "")),
            source_path=str(document.metadata.get("source_path", "")),
            content=document.page_content,
            images=[item for item in images.split("|") if item],
        )

    # 从 Chroma 中取出全部 chunks 做轻量关键词扫描，作为向量检索的补充召回。
    def _keyword_candidates(self, query: str, limit: int) -> list[DocumentChunk]:
        raw = self.store.get(include=["documents", "metadatas"])
        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])
        chunks: list[DocumentChunk] = []
        for document, metadata in zip(documents, metadatas):
            metadata = metadata or {}
            images = str(metadata.get("images", ""))
            chunks.append(
                DocumentChunk(
                    id=str(metadata.get("id", "")),
                    title=str(metadata.get("title", "")),
                    source_path=str(metadata.get("source_path", "")),
                    content=str(document),
                    images=[item for item in images.split("|") if item],
                )
            )
        return sorted(chunks, key=lambda chunk: keyword_score(query, chunk), reverse=True)[:limit]
