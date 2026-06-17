from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk
from scripts.inspect_retrieval import format_retrieval_results


def test_format_retrieval_results_includes_rank_scores_sources_and_images():
    results = [
        RetrievedChunk(
            chunk=DocumentChunk(
                id="doc::0",
                title="页面编辑器/简介",
                source_path="页面编辑器/简介.md",
                content="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                images=["页面编辑器/1.png"],
            ),
            score=0.91,
        )
    ]

    output = format_retrieval_results("页面编辑器有哪些区域？", results)

    assert "查询: 页面编辑器有哪些区域？" in output
    assert "Rank 1" in output
    assert "向量分: 0.91" in output
    assert "关键词分:" in output
    assert "综合分:" in output
    assert "页面编辑器/简介.md" in output
    assert "页面编辑器/1.png" in output
    assert "菜单栏" in output
