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
