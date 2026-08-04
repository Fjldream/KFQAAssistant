from app.rag.ingestion.structured_splitter import (
    HeadingBlock,
    TextBlock,
    build_sections,
    parse_heading_blocks,
)


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


def test_build_sections_groups_content_under_nearest_heading():
    blocks = [
        HeadingBlock(level=1, text="简介"),
        TextBlock("第一段。"),
        HeadingBlock(level=2, text="工具栏"),
        TextBlock("第二段。"),
        HeadingBlock(level=1, text="关于"),
        TextBlock("第三段。"),
    ]
    sections = build_sections(blocks)
    assert sections == [
        ("# 简介", "第一段。"),
        ("# 简介\n## 工具栏", "第二段。"),
        ("# 关于", "第三段。"),
    ]


def test_build_sections_skipped_level_attaches_to_nearest_ancestor():
    blocks = [
        HeadingBlock(level=1, text="教程"),
        HeadingBlock(level=3, text="发布"),
        TextBlock("内容。"),
    ]
    sections = build_sections(blocks)
    assert sections == [("# 教程\n### 发布", "内容。")]


def test_build_sections_no_headings_returns_single_empty_chain_section():
    sections = build_sections([TextBlock("纯文本内容。")])
    assert sections == [("", "纯文本内容。")]


def test_build_sections_preamble_before_first_heading_is_own_section():
    blocks = [TextBlock("文档开头。"), HeadingBlock(level=1, text="正文"), TextBlock("内容。")]
    sections = build_sections(blocks)
    assert sections == [("", "文档开头。"), ("# 正文", "内容。")]


from app.rag.ingestion.structured_splitter import split_oversized_section


def test_split_oversized_section_prefers_paragraph_boundaries():
    body = "\n\n".join(["第一段说明文字。", "第二段说明文字。", "第三段说明文字。", "第四段说明文字。"])
    pieces = split_oversized_section(body, chunk_size=12, chunk_overlap=0)
    assert len(pieces) == 4
    assert pieces[0] == "第一段说明文字。"
    assert all("段说明文字。" in piece for piece in pieces)


def test_split_oversized_section_merges_small_paragraphs_up_to_limit():
    body = "\n\n".join(["段一。", "段二。", "段三。", "段四。", "段五。"])
    pieces = split_oversized_section(body, chunk_size=16, chunk_overlap=0)
    # 每段 3 字 + 空行 2 字：16 字上限可容纳约 3 段
    assert len(pieces) < 5
    assert all(len(piece) <= 16 for piece in pieces)


def test_split_oversized_section_falls_back_to_character_split_for_long_paragraph():
    body = "X" * 100
    pieces = split_oversized_section(body, chunk_size=30, chunk_overlap=5)
    assert pieces[0] == "X" * 30
    assert pieces[1].startswith("X" * 5)
