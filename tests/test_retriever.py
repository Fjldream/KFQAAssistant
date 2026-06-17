from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk, RetrieverService
from app.rag.vector_store import combined_score, diversify_results, keyword_score


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


def test_combined_score_adds_vector_score_and_weighted_keyword_score():
    chunk = DocumentChunk(
        id="doc::0",
        title="页面编辑器/简介",
        source_path="页面编辑器/简介.md",
        content="页面编辑器包括菜单栏。",
    )
    item = RetrievedChunk(chunk=chunk, score=0.5)

    assert combined_score("页面编辑器有哪些区域？", item) == 0.5 + keyword_score("页面编辑器有哪些区域？", chunk) * 0.08


def test_diversify_results_prefers_different_sources_before_filling_duplicates():
    results = [
        RetrievedChunk(
            chunk=DocumentChunk(id="a::0", title="A", source_path="A.md", content="高分片段"),
            score=0.95,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="a::1", title="A", source_path="A.md", content="次高分片段"),
            score=0.94,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="b::0", title="B", source_path="B.md", content="不同来源"),
            score=0.80,
        ),
    ]

    diversified = diversify_results(results, top_k=2)

    assert [item.chunk.id for item in diversified] == ["a::0", "b::0"]


def test_diversify_results_fills_remaining_slots_with_high_score_duplicates():
    results = [
        RetrievedChunk(
            chunk=DocumentChunk(id="a::0", title="A", source_path="A.md", content="高分片段"),
            score=0.95,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="a::1", title="A", source_path="A.md", content="次高分片段"),
            score=0.94,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="b::0", title="B", source_path="B.md", content="不同来源"),
            score=0.80,
        ),
    ]

    diversified = diversify_results(results, top_k=3)

    assert [item.chunk.id for item in diversified] == ["a::0", "b::0", "a::1"]
