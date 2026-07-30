from app.rag.context_builder import build_context_blocks, format_context_blocks
from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk


def test_context_builder_includes_source_path_images_and_snippet():
    retrieved = [
        RetrievedChunk(
            DocumentChunk(
                id="guide.md::0",
                title="采集工程",
                source_path="数采管理/工程开发-Windows.md",
                content="点击新建工程。",
                images=["数采管理/1.png"],
            ),
            score=0.9,
        )
    ]

    blocks = build_context_blocks(retrieved)
    contexts = format_context_blocks(blocks)

    assert blocks[0].evidence_id == "资料 1"
    assert blocks[0].images == ["数采管理/1.png"]
    assert "相关图片：数采管理/1.png" in contexts[0]


def test_context_builder_formats_score_when_present():
    retrieved = [
        RetrievedChunk(
            DocumentChunk(
                id="guide.md::0",
                title="采集工程",
                source_path="数采管理/工程开发-Windows.md",
                content="点击新建工程。",
                images=[],
            ),
            score=0.9123,
        )
    ]

    contexts = format_context_blocks(build_context_blocks(retrieved))

    assert "相关分数：0.91" in contexts[0]
