from bs4 import BeautifulSoup

from app.rag.image_resolver import IMAGE_PATTERN


# 压缩多余空行，保留段落边界，让后续切块时文本更稳定。
def normalize_blank_lines(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    compact: list[str] = []
    blank_count = 0
    for line in lines:
        if line.strip():
            blank_count = 0
            compact.append(line)
        else:
            blank_count += 1
            if blank_count <= 1:
                compact.append("")
    return "\n".join(compact).strip()


# 清洗 Markdown 正文：移除图片标记，图片路径会单独存入 metadata。
def clean_markdown(text: str) -> str:
    without_images = IMAGE_PATTERN.sub("", text)
    return normalize_blank_lines(without_images)


# 清洗 HTML 正文：去掉脚本和样式，只保留可用于检索的文字内容。
def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    main = soup.select_one("#write") or soup.body or soup
    text = main.get_text("\n")
    return normalize_blank_lines(text)
