from pathlib import Path
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup


IMAGE_PATTERN = re.compile(r"!\[[^\]]*]\(([^)]+)\)")
HTML_IMAGE_PATTERN = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
IMAGE_MARKER_PATTERN = re.compile(r"\[\[KF_IMAGE_\d+]]")


# 为图片生成内部位置标记；这些标记只用于切块阶段，不会进入最终向量库文本。
def make_image_marker(index: int) -> str:
    return f"[[KF_IMAGE_{index}]]"


# 从 Markdown 正文中提取所有图片引用路径，例如 ![](./1.png)。
def extract_markdown_images(text: str) -> list[str]:
    return [match.strip() for match in IMAGE_PATTERN.findall(text) if match.strip()]


# 从 HTML 正文中提取 img 标签的 src，用于让 HTML 手册也能返回截图。
def extract_html_images(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    images: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            images.append(str(src).strip())
    return [image for image in images if image]


# 将 Markdown 图片语法替换为内部位置标记，并返回标记到原始图片路径的映射。
def mark_markdown_images(text: str) -> tuple[str, dict[str, str]]:
    markers: dict[str, str] = {}

    def replace_markdown_image(match: re.Match[str]) -> str:
        raw_path = match.group(1).strip()
        marker = make_image_marker(len(markers))
        markers[marker] = raw_path
        return f"\n{marker}\n"

    def replace_html_image(match: re.Match[str]) -> str:
        raw_path = match.group(1).strip()
        marker = make_image_marker(len(markers))
        markers[marker] = raw_path
        return f"\n{marker}\n"

    marked_text = IMAGE_PATTERN.sub(replace_markdown_image, text)
    marked_text = HTML_IMAGE_PATTERN.sub(replace_html_image, marked_text)
    return marked_text, markers


# 将 HTML img 标签替换为内部位置标记，并返回标记到原始图片路径的映射。
def mark_html_images(html: str) -> tuple[str, dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    markers: dict[str, str] = {}
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        marker = make_image_marker(len(markers))
        markers[marker] = str(src).strip()
        img.replace_with(soup.new_string(f"\n{marker}\n"))
    return str(soup), markers


# 将文档中的相对图片路径解析成相对知识库根目录的 POSIX 路径。
def resolve_image_path(raw_path: str, document_path: Path, root_dir: Path) -> str:
    normalized = raw_path.replace("\\", "/").strip()
    parsed = urlparse(normalized)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return normalized

    if normalized.startswith("/"):
        root_relative = normalized.lstrip("/")
        candidate = (root_dir / root_relative).resolve()
        public_candidate = (root_dir / "public" / root_relative).resolve()
        if not candidate.exists() and public_candidate.exists():
            candidate = public_candidate
    else:
        candidate = (document_path.parent / normalized).resolve()
    try:
        return candidate.relative_to(root_dir.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()
