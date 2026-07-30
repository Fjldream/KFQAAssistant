from pathlib import Path
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk


KEYWORD_SCORE_WEIGHT = 0.08
NEIGHBOR_SCORE_PENALTY = 0.001


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
    if any(word in query for word in ["启动", "运行"]) and "工程" in query:
        expanded.extend(["发布", "部署", "启动", "运维中心", "运行节点", "添加端口"])
    if "数据组态工程" in query or "数据源工程" in query:
        expanded.extend(["数据组态工程的启动", "数据组态工程的创建", "数据APP组态", "数据源接口APP"])
    if "采集工程" in query or "数采工程" in query:
        expanded.extend(["数采工程", "数采管理", "驱动", "设备", "变量", "发布工程", "部署启动"])
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
    score += workflow_intent_score(query, text)
    return score


# 针对“启动/运行工程”问题，提升包含发布、运维中心、部署、启动等完整流程证据的片段。
def workflow_intent_score(query: str, text: str) -> float:
    if not (any(word in query for word in ["启动", "运行"]) and "工程" in query):
        return 0.0

    workflow_terms = ["发布", "运维中心", "运行的节点", "添加端口", "部署", "启动"]
    matched_count = sum(1 for term in workflow_terms if term in text)
    if matched_count < 3:
        return 0.0
    return float(matched_count * 2)


# 计算最终排序分：向量相关性分加上加权后的关键词匹配分。
def combined_score(query: str, item: RetrievedChunk) -> float:
    return (item.score or 0.0) + keyword_score(query, item.chunk) * KEYWORD_SCORE_WEIGHT


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


# 根据当前 chunk ID 推导同一文档的前后相邻 chunk ID。
def neighbor_chunk_ids(chunk_id: str, radius: int = 1) -> list[str]:
    source_path, separator, raw_index = chunk_id.rpartition("::")
    if not separator or not raw_index.isdigit():
        return []
    index = int(raw_index)
    return [f"{source_path}::{neighbor}" for neighbor in range(max(0, index - radius), index + radius + 1) if neighbor != index]


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

    # 将业务 chunk 转换为 LangChain Document，统一全量和增量写入格式。
    def _chunks_to_documents(self, chunks: list[DocumentChunk]) -> tuple[list[Document], list[str]]:
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
        return documents, ids

    # 只为新增或修改文档的 chunks 生成 embedding 并写入 Chroma。
    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        documents, ids = self._chunks_to_documents(chunks)
        if ids:
            self.store.add_documents(documents=documents, ids=ids)
        return len(ids)

    # 按文档来源删除全部旧 chunks，返回实际删除数量。
    def delete_sources(self, source_paths: list[str]) -> int:
        ids: list[str] = []
        for source_path in source_paths:
            result = self.store.get(where={"source_path": source_path})
            ids.extend(str(item) for item in result.get("ids", []))
        if ids:
            self.store.delete(ids=ids)
        return len(ids)

    # 将切好的 chunks 写入 Chroma，返回写入数量，供索引构建脚本展示进度。
    def rebuild(self, chunks: list[DocumentChunk]) -> int:
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.store.reset_collection()
        return self.add_chunks(chunks)

    # 返回当前 Chroma collection 中的文档数量，用于健康检查和索引状态展示。
    def count(self) -> int:
        return int(self.store._collection.count())

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
            key=lambda item: combined_score(query, item),
            reverse=True,
        )
        diversified = diversify_results(ranked, top_k)
        return self._include_neighbor_chunks(diversified)

    # 为主要命中结果补充同文档前后相邻 chunk，让操作流程回答能拿到更完整上下文。
    def _include_neighbor_chunks(self, primary_results: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not primary_results:
            return []

        selected_ids = {item.chunk.id for item in primary_results}
        neighbor_ids_by_primary: dict[str, list[str]] = {}
        neighbor_ids: list[str] = []
        for item in primary_results:
            for chunk_id in neighbor_chunk_ids(item.chunk.id):
                if chunk_id not in selected_ids and chunk_id not in neighbor_ids:
                    neighbor_ids.append(chunk_id)
                    neighbor_ids_by_primary.setdefault(item.chunk.id, []).append(chunk_id)

        if not neighbor_ids:
            return primary_results

        neighbor_results = {item.chunk.id: item for item in self._chunks_by_ids(neighbor_ids)}
        expanded_results: list[RetrievedChunk] = []
        for item in primary_results:
            expanded_results.append(item)
            for chunk_id in neighbor_ids_by_primary.get(item.chunk.id, []):
                neighbor = neighbor_results.get(chunk_id)
                if neighbor:
                    expanded_results.append(neighbor)
        return expanded_results

    # 按 chunk ID 从 Chroma 读回完整 DocumentChunk，用于邻居上下文补全。
    def _chunks_by_ids(self, chunk_ids: list[str]) -> list[RetrievedChunk]:
        raw = self.store.get(ids=chunk_ids, include=["documents", "metadatas"])
        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])
        results: list[RetrievedChunk] = []
        for document, metadata in zip(documents, metadatas):
            metadata = metadata or {}
            chunk = self._document_to_chunk(Document(page_content=str(document), metadata=metadata))
            results.append(RetrievedChunk(chunk=chunk, score=0.0 - NEIGHBOR_SCORE_PENALTY))
        return results

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
