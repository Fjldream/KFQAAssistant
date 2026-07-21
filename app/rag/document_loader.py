from pathlib import Path

from app.rag.image_resolver import mark_html_images, mark_markdown_images, resolve_image_path
from app.rag.models import ManualDocument
from app.rag.text_cleaner import clean_html, clean_markdown


# 根据文件路径生成文档标题，保留目录层级作为检索上下文。
def _title_from_path(path: Path, root_dir: Path) -> str:
    relative = path.relative_to(root_dir)
    return "/".join(relative.with_suffix("").parts)


# 判断 HTML 文件旁边是否有同名 Markdown，用于避免重复索引同一页面。
def _has_markdown_twin(path: Path) -> bool:
    return path.with_suffix(".md").exists()


# 发现所有可索引手册路径；同名 Markdown 和 HTML 同时存在时只选择 Markdown。
def discover_document_paths(root_dir: Path) -> list[Path]:
    root_dir = root_dir.resolve()
    paths = sorted(root_dir.rglob("*"))
    return [
        path
        for path in paths
        if path.is_file()
        and (
            path.suffix.lower() == ".md"
            or (path.suffix.lower() == ".html" and not _has_markdown_twin(path))
        )
    ]


# 加载并清洗一篇指定手册，供增量索引只处理发生变化的文件。
def load_document(path: Path, root_dir: Path) -> ManualDocument | None:
    root_dir = root_dir.resolve()
    path = path.resolve()
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".md":
        marked_raw, raw_image_markers = mark_markdown_images(raw)
        content = clean_markdown(marked_raw)
    else:
        marked_raw, raw_image_markers = mark_html_images(raw)
        content = clean_html(marked_raw)

    image_markers = {
        marker: resolve_image_path(raw_path, path, root_dir) for marker, raw_path in raw_image_markers.items()
    }
    if not content.strip():
        return None
    return ManualDocument(
        title=_title_from_path(path, root_dir),
        source_path=path.relative_to(root_dir).as_posix(),
        content=content,
        images=list(image_markers.values()),
        image_markers=image_markers,
    )


# 遍历手册目录并加载文本资料，优先 Markdown，必要时回退到清洗后的 HTML。
def load_documents(root_dir: Path) -> list[ManualDocument]:
    documents = [load_document(path, root_dir) for path in discover_document_paths(root_dir)]
    return [document for document in documents if document is not None]
