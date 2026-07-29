from pathlib import Path

from app.rag.document_loader import discover_document_paths, load_document, load_documents


# 验证文档发现会排除已有 Markdown 双胞胎的 HTML 文件。
def test_discover_document_paths_prefers_markdown(tmp_path: Path):
    (tmp_path / "guide.md").write_text("# Markdown", encoding="utf-8")
    (tmp_path / "guide.html").write_text("<h1>HTML</h1>", encoding="utf-8")

    paths = discover_document_paths(tmp_path)

    assert paths == [(tmp_path / "guide.md").resolve()]


# 验证可以只加载增量更新指定的单篇文档。
def test_load_document_loads_one_selected_file(tmp_path: Path):
    path = tmp_path / "guide.md"
    path.write_text("# 创建工程\n点击新建工程。", encoding="utf-8")

    document = load_document(path, tmp_path)

    assert document is not None
    assert document.source_path == "guide.md"
    assert "点击新建工程" in document.content


def test_loader_prefers_markdown_over_html(tmp_path: Path):
    root = tmp_path / "help"
    page_dir = root / "功能模块" / "页面编辑器"
    page_dir.mkdir(parents=True)
    (page_dir / "简介.md").write_text("# 简介\n\nMarkdown 正文\n![](./1.png)", encoding="utf-8")
    (page_dir / "简介.html").write_text("<h1>简介</h1><p>HTML 正文</p>", encoding="utf-8")
    (page_dir / "1.png").write_bytes(b"png")

    docs = load_documents(root)

    assert len(docs) == 1
    assert "Markdown 正文" in docs[0].content
    assert "[[KF_IMAGE_0]]" in docs[0].content
    assert docs[0].source_path.endswith("简介.md")
    assert docs[0].images == ["功能模块/页面编辑器/1.png"]
    assert docs[0].image_markers == {"[[KF_IMAGE_0]]": "功能模块/页面编辑器/1.png"}


def test_loader_falls_back_to_html(tmp_path: Path):
    root = tmp_path / "help"
    page_dir = root / "关于"
    page_dir.mkdir(parents=True)
    (page_dir / "客户端.html").write_text(
        "<h1>客户端</h1><p>支持 Windows。</p><img src='./client.png'>",
        encoding="utf-8",
    )
    (page_dir / "client.png").write_bytes(b"png")

    docs = load_documents(root)

    assert len(docs) == 1
    assert "支持 Windows" in docs[0].content
    assert "[[KF_IMAGE_0]]" in docs[0].content
    assert docs[0].images == ["关于/client.png"]
    assert docs[0].image_markers == {"[[KF_IMAGE_0]]": "关于/client.png"}
