from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk


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
        results = self.store.similarity_search_with_relevance_scores(query, k=top_k)
        retrieved: list[RetrievedChunk] = []
        for document, score in results:
            images = document.metadata.get("images", "")
            retrieved.append(
                RetrievedChunk(
                    chunk=DocumentChunk(
                        id=str(document.metadata.get("id", "")),
                        title=str(document.metadata.get("title", "")),
                        source_path=str(document.metadata.get("source_path", "")),
                        content=document.page_content,
                        images=[item for item in images.split("|") if item],
                    ),
                    score=float(score),
                )
            )
        return retrieved
