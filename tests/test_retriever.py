from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk, RetrieverService
from app.rag.vector_store import keyword_score


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


def test_keyword_score_boosts_system_environment_document():
    correct = DocumentChunk(
        id="env::0",
        title="关于/系统环境要求/客户端/客户端",
        source_path="关于/系统环境要求/客户端/客户端.md",
        content="客户端参数。软件要求：Windows、Linux、Chrome 浏览器。",
    )
    wrong = DocumentChunk(
        id="window::0",
        title="页面编辑器/工具箱/UI组件/Windows窗脚本属性",
        source_path="页面编辑器/工具箱/UI组件/Windows窗脚本属性.md",
        content="描述 Windows 窗组件的位置、宽度和高度。",
    )

    query = "客户端对操作系统有什么要求？"

    assert keyword_score(query, correct) > keyword_score(query, wrong)
