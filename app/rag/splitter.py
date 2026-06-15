from app.rag.image_resolver import IMAGE_MARKER_PATTERN
from app.rag.models import DocumentChunk, ManualDocument
from app.rag.text_cleaner import normalize_blank_lines


# 按固定长度切分文本，并保留少量重叠，避免关键语义被切断。
def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - chunk_overlap)
    return chunks


# 确保每个 chunk 至少带有文档标题上下文，提升向量检索命中质量。
def _with_title_context(document: ManualDocument) -> str:
    if document.content.lstrip().startswith("#"):
        return document.content
    return f"# {document.title}\n\n{document.content}"


# 从 chunk 文本里找出图片标记对应的图片路径。
def _images_for_chunk(content: str, document: ManualDocument) -> list[str]:
    images: list[str] = []
    for marker in IMAGE_MARKER_PATTERN.findall(content):
        image = document.image_markers.get(marker)
        if image and image not in images:
            images.append(image)
    return images


# 移除内部图片位置标记，避免标记进入向量库和最终回答来源片段。
def _remove_image_markers(content: str) -> str:
    return normalize_blank_lines(IMAGE_MARKER_PATTERN.sub("", content))


# 将清洗后的手册文档拆成可写入向量库的 DocumentChunk 列表。
def split_documents(
    documents: list[ManualDocument],
    chunk_size: int = 700,
    chunk_overlap: int = 100,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        text = _with_title_context(document)
        for index, content in enumerate(_split_text(text, chunk_size, chunk_overlap)):
            chunk_images = _images_for_chunk(content, document) if document.image_markers else document.images
            clean_content = _remove_image_markers(content)
            chunks.append(
                DocumentChunk(
                    id=f"{document.source_path}::{index}",
                    title=document.title,
                    source_path=document.source_path,
                    content=clean_content,
                    images=chunk_images,
                )
            )
    return chunks
