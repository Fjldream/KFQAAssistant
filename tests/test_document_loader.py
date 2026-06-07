from pathlib import Path

from app.rag.document_loader import load_documents


def test_loader_prefers_markdown_over_html(tmp_path: Path):
    root = tmp_path / "help"
    page_dir = root / "功能模块" / "页面编辑器"
    page_dir.mkdir(parents=True)
    (page_dir / "简介.md").write_text("# 简介\n\nMarkdown 正文\n![](./1.png)", encoding="utf-8")
    (page_dir / "简介.html").write_text("<h1>简介</h1><p>HTML 正文</p>", encoding="utf-8")
    (page_dir / "1.png").write_bytes(b"png")

    docs = load_documents(root)

    assert len(docs) == 1
    assert docs[0].content == "# 简介\n\nMarkdown 正文"
    assert docs[0].source_path.endswith("简介.md")
    assert docs[0].images == ["功能模块/页面编辑器/1.png"]


def test_loader_falls_back_to_html(tmp_path: Path):
    root = tmp_path / "help"
    page_dir = root / "关于"
    page_dir.mkdir(parents=True)
    (page_dir / "客户端.html").write_text("<h1>客户端</h1><p>支持 Windows。</p>", encoding="utf-8")

    docs = load_documents(root)

    assert len(docs) == 1
    assert "支持 Windows" in docs[0].content
