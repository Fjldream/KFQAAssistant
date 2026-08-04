import re

from bs4 import BeautifulSoup
from markdownify import markdownify as _markdownify

from app.rag.ingestion.image_resolver import IMAGE_PATTERN

_INLINE_STRIKE_PATTERN = re.compile(r"~~(.+?)~~")
_INLINE_LINK_PATTERN = re.compile(r"\[([^\]]+)]\([^)]*\)")
_INLINE_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")
_INLINE_ITALIC_PATTERN = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")


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


def _strip_inline_markdown(text: str) -> str:
    text = _INLINE_STRIKE_PATTERN.sub(r"\1", text)
    text = _INLINE_LINK_PATTERN.sub(r"\1", text)
    text = _INLINE_BOLD_PATTERN.sub(r"\1", text)
    text = _INLINE_ITALIC_PATTERN.sub(r"\1", text)
    text = _INLINE_CODE_PATTERN.sub(r"\1", text)
    # 还原 markdownify 0.14.1 的实际转义。经实证（真实 conda 环境 + 源码核对）：
    # 默认选项下（escape_asterisks=True、escape_underscores=True、escape_misc=False）
    # markdownify 只会把文本节点中的 `*` 转义为 `\*`、`_` 转义为 `\_`（如图片标记
    # [[KF_IMAGE_0]] 的下划线）。`~ { } ( ) # + - . ! | [ ] ` \` 等默认均不转义，
    # 若纳入反解会破坏正文中用户原有的反斜杠序列，故只反解 `_` 与 `*`。
    text = re.sub(r"\\([_*])", r"\1", text)
    return text


# 清洗 HTML 正文：去掉脚本和样式，转成带标题层级的 Markdown，只保留可用于检索的文字内容。
def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    main = soup.select_one("#write") or soup.body or soup
    text = _markdownify(str(main), heading_style="ATX")
    return normalize_blank_lines(_strip_inline_markdown(text))
