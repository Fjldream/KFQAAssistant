from dataclasses import dataclass

from app.rag.retriever import RetrievedChunk


@dataclass(frozen=True)
class ContextBlock:
    evidence_id: str
    title: str
    source_path: str
    content: str
    images: list[str]
    score: float | None


# 将检索结果转换成结构化资料块，保留资料编号、来源、图片和相关分数。
def build_context_blocks(retrieved: list[RetrievedChunk]) -> list[ContextBlock]:
    return [
        ContextBlock(
            evidence_id=f"资料 {index}",
            title=item.chunk.title,
            source_path=item.chunk.source_path,
            content=item.chunk.content,
            images=item.chunk.images,
            score=item.score,
        )
        for index, item in enumerate(retrieved, start=1)
    ]


# 将结构化资料块格式化为大模型可读上下文，降低模型漏看来源和图片信息的概率。
def format_context_blocks(blocks: list[ContextBlock]) -> list[str]:
    contexts: list[str] = []
    for block in blocks:
        lines = [
            f"[{block.evidence_id}]",
            f"标题：{block.title}",
            f"来源：{block.source_path}",
        ]
        if block.score is not None:
            lines.append(f"相关分数：{block.score:.2f}")
        if block.images:
            lines.append(f"相关图片：{', '.join(block.images)}")
        lines.extend(["内容：", block.content])
        contexts.append("\n".join(lines))
    return contexts
