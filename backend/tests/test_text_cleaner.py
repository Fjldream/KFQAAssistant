from app.rag.ingestion.text_cleaner import clean_html, clean_markdown


def test_clean_markdown_removes_image_markup_but_keeps_text():
    text = "# 简介\n\n页面编辑器如下。\n\n![](./1.png)\n"
    cleaned = clean_markdown(text)

    assert "页面编辑器如下" in cleaned
    assert "![]" not in cleaned


def test_clean_html_extracts_body_text_without_css():
    html = "<html><head><style>.x{}</style></head><body><h1>客户端</h1><p>支持 Windows。</p><script>x()</script></body></html>"
    cleaned = clean_html(html)

    assert "客户端" in cleaned
    assert "支持 Windows" in cleaned
    assert ".x" not in cleaned
    assert "x()" not in cleaned


from app.rag.ingestion.text_cleaner import _strip_inline_markdown


def test_clean_html_converts_headings_to_markdown():
    html = "<html><body><h1>客户端</h1><p>支持 <b>Windows</b>。</p><a href='/x'>详情</a></body></html>"
    cleaned = clean_html(html)
    assert cleaned.startswith("# 客户端")
    assert "支持 Windows" in cleaned
    assert "**" not in cleaned
    assert "[详情]" not in cleaned


def test_strip_inline_markdown_keeps_heading_and_list_structure():
    text = "# 标题\n\n- **加粗项**\n- `代码` 与 [链接](https://example.com)"
    cleaned = _strip_inline_markdown(text)
    assert cleaned == "# 标题\n\n- 加粗项\n- 代码 与 链接"


def test_strip_inline_markdown_does_not_touch_image_markers():
    text = "正文。\n[[KF_IMAGE_0]]\n"
    assert _strip_inline_markdown(text) == text


def test_strip_inline_markdown_unescapes_image_marker():
    # 回归：markdownify 会把 [[KF_IMAGE_0]] 转义为 [[KF\_IMAGE\_0]]，
    # 还原标记中的下划线正是加入 unescape 的唯一动机，必须直接覆盖该路径。
    assert _strip_inline_markdown(r"[[KF\_IMAGE\_0]]") == "[[KF_IMAGE_0]]"


def test_strip_inline_markdown_unescapes_asterisks_and_underscores():
    # markdownify 0.14.1 默认（escape_asterisks=True、escape_underscores=True、
    # escape_misc=False）实测只转义 `*` 和 `_`；二者都必须被还原。
    assert _strip_inline_markdown(r"a \* b \_ c") == "a * b _ c"


def test_strip_inline_markdown_does_not_unescape_markdownify_non_escaped_chars():
    # 除 `*`、`_` 外，markdownify 0.14.1 默认不转义 ~ { } ( ) # + - . ! | [ ] ` \ 等，
    # 正文中这些反斜杠序列属于用户原文，不得被误反解（防字符类过宽回归）。
    text = r"~ { } ( ) # + - . ! | [ ] 与 ` 和 \ 均原样"
    assert _strip_inline_markdown(text) == text
