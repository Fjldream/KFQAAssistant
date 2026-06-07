from app.rag.models import ManualDocument
from app.rag.splitter import split_documents


def test_splitter_preserves_metadata_and_images():
    doc = ManualDocument(
        title="功能模块/页面编辑器/简介",
        source_path="功能模块/页面编辑器/简介.md",
        content="# 简介\n\n页面编辑器用于编辑页面。\n\n## 工具栏\n\n工具栏包括保存、撤销、重做。",
        images=["功能模块/页面编辑器/1.png"],
    )

    chunks = split_documents([doc], chunk_size=30, chunk_overlap=5)

    assert chunks
    assert chunks[0].title == doc.title
    assert chunks[0].source_path == doc.source_path
    assert chunks[0].images == doc.images
    assert "页面编辑器" in chunks[0].content


def test_splitter_adds_stable_ids():
    doc = ManualDocument(title="关于/客户端", source_path="关于/客户端.md", content="客户端支持 Windows。", images=[])

    chunks = split_documents([doc], chunk_size=50, chunk_overlap=5)

    assert chunks[0].id == "关于/客户端.md::0"
