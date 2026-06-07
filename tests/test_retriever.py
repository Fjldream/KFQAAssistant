from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk, RetrieverService


class FakeVectorStore:
    def similarity_search(self, query: str, top_k: int):
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="a::0",
                    title="页面编辑器/简介",
                    source_path="页面编辑器/简介.md",
                    content="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                    images=["页面编辑器/1.png"],
                ),
                score=0.91,
            )
        ]


def test_retriever_returns_ranked_chunks():
    service = RetrieverService(vector_store=FakeVectorStore(), top_k=5)

    results = service.retrieve("页面编辑器有哪些区域？")

    assert results[0].score == 0.91
    assert results[0].chunk.images == ["页面编辑器/1.png"]
