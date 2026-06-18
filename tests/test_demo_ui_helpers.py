from pathlib import Path

from demo.ui_helpers import evidence_label, resolved_source_images
from demo.ui_helpers import score_label, snippet_preview


# 验证多个资料编号会被合并成适合页面展示的文本。
def test_evidence_label_joins_source_evidence_ids():
    source = {"evidence_ids": ["资料 1", "资料 2"]}

    assert evidence_label(source) == "资料 1、资料 2"


# 验证来源缺少资料编号时会显示兜底文本。
def test_evidence_label_uses_fallback_when_source_has_no_evidence_ids():
    source = {"title": "页面编辑器"}

    assert evidence_label(source) == "资料"


# 验证相似度分数会被格式化为固定两位小数。
def test_score_label_formats_optional_score():
    assert score_label({"score": 0.9123}) == "相似度 0.91"
    assert score_label({"score": None}) == "相似度 -"


# 验证图片解析会标记本地文件是否真实存在。
def test_resolved_source_images_marks_missing_files(tmp_path: Path):
    data_dir = tmp_path / "help"
    image_path = data_dir / "html" / "about" / "1.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"png")
    source = {"images": ["html/about/1.png", "html/about/missing.png"]}

    images = resolved_source_images(source, data_dir=data_dir)

    assert images == [
        {"path": "html/about/1.png", "resolved_path": str(image_path), "exists": True},
        {"path": "html/about/missing.png", "resolved_path": None, "exists": False},
    ]


# 验证来源片段会压缩空白并限制展示长度。
def test_snippet_preview_collapses_whitespace_and_limits_length():
    source = {"snippet": "# 标题\n\n第一段内容很长很长很长"}

    assert snippet_preview(source, limit=10) == "# 标题 第一段内容..."
