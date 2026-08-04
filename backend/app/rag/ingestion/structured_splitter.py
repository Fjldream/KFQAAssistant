import re
from dataclasses import dataclass

from app.rag.ingestion.image_resolver import IMAGE_MARKER_PATTERN
from app.rag.ingestion.text_cleaner import normalize_blank_lines
from app.rag.models import DocumentChunk, ManualDocument

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")


@dataclass(frozen=True)
class HeadingBlock:
    level: int
    text: str


@dataclass(frozen=True)
class TextBlock:
    text: str


Block = HeadingBlock | TextBlock


def parse_heading_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    current: list[str] = []
    in_fence = False
    fence_marker = ""

    def flush_text() -> None:
        if current:
            blocks.append(TextBlock("\n".join(current).strip()))
            current.clear()

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        fence_match = FENCE_PATTERN.match(line)
        if in_fence:
            current.append(line)
            if fence_match and fence_match.group(1) == fence_marker:
                in_fence = False
            continue
        if fence_match:
            in_fence = True
            fence_marker = fence_match.group(1)
            current.append(line)
            continue
        heading = HEADING_PATTERN.match(line)
        if heading:
            flush_text()
            blocks.append(HeadingBlock(level=len(heading.group(1)), text=heading.group(2).strip()))
        else:
            current.append(line)
    flush_text()
    return blocks


def build_sections(blocks: list[Block]) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    chain: dict[int, str] = {}
    current_chain = ""
    current_body: list[str] = []

    def flush() -> None:
        if current_body:
            sections.append((current_chain, "\n".join(current_body).strip()))
        current_body.clear()

    for block in blocks:
        if isinstance(block, TextBlock):
            current_body.append(block.text)
            continue
        flush()
        chain = {level: text for level, text in chain.items() if level < block.level}
        chain[block.level] = block.text
        current_chain = "\n".join(f"{'#' * level} {text}" for level, text in sorted(chain.items()))
    flush()
    return sections


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """复用旧固定长度切分：段落内超长时的最终兜底。"""
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


def split_oversized_section(body: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body) if paragraph.strip()]
    pieces: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                pieces.append("\n\n".join(current))
                current, current_len = [], 0
            pieces.extend(_split_text(paragraph, chunk_size, chunk_overlap))
            continue
        if current and current_len + len(paragraph) + 2 > chunk_size:
            pieces.append("\n\n".join(current))
            current, current_len = [], 0
        current.append(paragraph)
        current_len += len(paragraph) + 2
    if current:
        pieces.append("\n\n".join(current))
    return [piece for piece in pieces if piece.strip()]


def _images_for_chunk(content: str, document: ManualDocument) -> list[str]:
    images: list[str] = []
    for marker in IMAGE_MARKER_PATTERN.findall(content):
        image = document.image_markers.get(marker)
        if image and image not in images:
            images.append(image)
    return images


def _remove_image_markers(content: str) -> str:
    return normalize_blank_lines(IMAGE_MARKER_PATTERN.sub("", content))


def split_structured(document: ManualDocument, chunk_size: int, chunk_overlap: int) -> list[DocumentChunk]:
    sections = build_sections(parse_heading_blocks(document.content))
    chunks: list[DocumentChunk] = []
    index = 0
    for title_chain, body in sections:
        if title_chain:
            prefix = f"{title_chain}\n\n"
            units = [body] if len(body) <= chunk_size else split_oversized_section(body, chunk_size, chunk_overlap)
        else:
            # 无标题退化路径：补文档标题作为上下文，走旧固定长度切分
            prefix = ""
            body_full = f"# {document.title}\n\n{body}"
            units = _split_text(body_full, chunk_size, chunk_overlap)
        for unit in units:
            content_with_prefix = f"{prefix}{unit}"
            chunk_images = _images_for_chunk(content_with_prefix, document) if document.image_markers else document.images
            chunks.append(
                DocumentChunk(
                    id=f"{document.source_path}::{index}",
                    title=document.title,
                    source_path=document.source_path,
                    content=_remove_image_markers(content_with_prefix),
                    images=chunk_images,
                )
            )
            index += 1
    return chunks
