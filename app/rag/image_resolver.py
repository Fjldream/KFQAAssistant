from pathlib import Path
import re


IMAGE_PATTERN = re.compile(r"!\[[^\]]*]\(([^)]+)\)")


# 从 Markdown 正文中提取所有图片引用路径，例如 ![](./1.png)。
def extract_markdown_images(text: str) -> list[str]:
    return [match.strip() for match in IMAGE_PATTERN.findall(text) if match.strip()]


# 将文档中的相对图片路径解析成相对知识库根目录的 POSIX 路径。
def resolve_image_path(raw_path: str, document_path: Path, root_dir: Path) -> str:
    normalized = raw_path.replace("\\", "/").strip()
    candidate = (document_path.parent / normalized).resolve()
    try:
        return candidate.relative_to(root_dir.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()
