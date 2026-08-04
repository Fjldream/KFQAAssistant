import re
from dataclasses import dataclass

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
