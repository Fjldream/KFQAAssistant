from pathlib import Path

from app.rag.image_resolver import extract_html_images, extract_markdown_images, resolve_image_path
from app.rag.models import ManualDocument
from app.rag.text_cleaner import clean_html, clean_markdown


# 根据文件路径生成文档标题，保留目录层级作为检索上下文。
def _title_from_path(path: Path, root_dir: Path) -> str:
    relative = path.relative_to(root_dir)
    return "/".join(relative.with_suffix("").parts)


# 判断 HTML 文件旁边是否有同名 Markdown，用于避免重复索引同一页面。
def _has_markdown_twin(path: Path) -> bool:
    return path.with_suffix(".md").exists()


# 遍历手册目录并加载文本资料，优先 Markdown，必要时回退到清洗后的 HTML。
def load_documents(root_dir: Path) -> list[ManualDocument]:
    root_dir = root_dir.resolve()
    paths = sorted(root_dir.rglob("*"))
    selected = [
        path
        for path in paths
        if path.is_file()
        and (
            path.suffix.lower() == ".md"
            or (path.suffix.lower() == ".html" and not _has_markdown_twin(path))
        )
    ]

    documents: list[ManualDocument] = []
    for path in selected:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".md":
            raw_images = extract_markdown_images(raw)
            images = [resolve_image_path(item, path, root_dir) for item in raw_images]
            content = clean_markdown(raw)
        else:
            raw_images = extract_html_images(raw)
            images = [resolve_image_path(item, path, root_dir) for item in raw_images]
            content = clean_html(raw)

        if content.strip():
            documents.append(
                ManualDocument(
                    title=_title_from_path(path, root_dir),
                    source_path=path.relative_to(root_dir).as_posix(),
                    content=content,
                    images=images,
                )
            )
    return documents
