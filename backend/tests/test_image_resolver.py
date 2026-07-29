from pathlib import Path

from app.rag.image_resolver import extract_markdown_images, mark_html_images, mark_markdown_images, resolve_image_path


def test_extract_markdown_images_supports_windows_style_paths():
    text = "工具栏如下：\n![](.\u005c2.png)\n![页面](./page.png)"
    assert extract_markdown_images(text) == [".\\2.png", "./page.png"]


def test_mark_markdown_images_preserves_image_position_with_marker():
    text = "第一步。\n![](./1.png)\n第二步。"

    marked, markers = mark_markdown_images(text)

    assert "[[KF_IMAGE_0]]" in marked
    assert markers == {"[[KF_IMAGE_0]]": "./1.png"}


def test_mark_markdown_images_also_marks_inline_html_images():
    text = "第一步。\n![](./1.png)\n第二步。\n<img src='.\\2.png' alt='2'/>"

    marked, markers = mark_markdown_images(text)

    assert "[[KF_IMAGE_0]]" in marked
    assert "[[KF_IMAGE_1]]" in marked
    assert markers == {
        "[[KF_IMAGE_0]]": "./1.png",
        "[[KF_IMAGE_1]]": ".\\2.png",
    }


def test_mark_html_images_preserves_image_position_with_marker():
    html = "<p>第一步。</p><img src='./1.png'><p>第二步。</p>"

    marked, markers = mark_html_images(html)

    assert "[[KF_IMAGE_0]]" in marked
    assert markers == {"[[KF_IMAGE_0]]": "./1.png"}


def test_resolve_image_path_returns_posix_relative_path(tmp_path: Path):
    doc_path = tmp_path / "docs" / "intro.md"
    doc_path.parent.mkdir()
    doc_path.write_text("demo", encoding="utf-8")
    image_path = doc_path.parent / "2.png"
    image_path.write_bytes(b"png")

    resolved = resolve_image_path(".\\2.png", doc_path, tmp_path)

    assert resolved == "docs/2.png"
