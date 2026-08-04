from app.rag.ingestion.structured_splitter import HeadingBlock, TextBlock, parse_heading_blocks


def test_parse_heading_blocks_recognizes_atx_headings():
    text = "# 简介\n\n正文第一段。\n\n## 工具栏\n\n正文第二段。"
    blocks = parse_heading_blocks(text)
    assert blocks == [
        HeadingBlock(level=1, text="简介"),
        TextBlock("正文第一段。"),
        HeadingBlock(level=2, text="工具栏"),
        TextBlock("正文第二段。"),
    ]


def test_parse_heading_blocks_skips_headings_inside_code_fence():
    text = "```python\n# 这不是标题\nprint(1)\n```\n\n正文。"
    blocks = parse_heading_blocks(text)
    assert blocks == [TextBlock("```python\n# 这不是标题\nprint(1)\n```\n\n正文。")]


def test_parse_heading_blocks_requires_space_after_hash():
    text = "#标题\n\n## 真标题"
    blocks = parse_heading_blocks(text)
    assert blocks == [TextBlock("#标题"), HeadingBlock(level=2, text="真标题")]
