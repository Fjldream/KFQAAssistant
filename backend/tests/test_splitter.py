from app.rag.models import ManualDocument
from app.rag.ingestion.splitter import split_documents


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


def test_splitter_attaches_only_images_marked_inside_each_chunk():
    doc = ManualDocument(
        title="教程/采集工程",
        source_path="教程/采集工程.md",
        content=(
            "创建采集工程第一步。\n"
            "[[KF_IMAGE_0]]\n"
            + ("A" * 80)
            + "\n创建采集工程第二步。\n"
            "[[KF_IMAGE_1]]\n"
        ),
        images=["教程/1.png", "教程/2.png"],
        image_markers={
            "[[KF_IMAGE_0]]": "教程/1.png",
            "[[KF_IMAGE_1]]": "教程/2.png",
        },
    )

    chunks = split_documents([doc], chunk_size=80, chunk_overlap=0)

    assert chunks[0].images == ["教程/1.png"]
    assert chunks[-1].images == ["教程/2.png"]
    assert all("[[KF_IMAGE_" not in chunk.content for chunk in chunks)
