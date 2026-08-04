"""文档切分入口：委托给结构化切分器，保留旧固定长度切分作为无标题文档的退化路径。"""
from app.rag.ingestion.structured_splitter import split_structured
from app.rag.models import DocumentChunk, ManualDocument

DEFAULT_CHUNK_SIZE = 700
DEFAULT_CHUNK_OVERLAP = 100


def split_documents(
    documents: list[ManualDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        chunks.extend(split_structured(document, chunk_size, chunk_overlap))
    return chunks
