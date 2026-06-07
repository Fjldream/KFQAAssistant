from dataclasses import dataclass, field


# 表示一篇已经清洗好的手册文档，是进入切块流程前的统一数据结构。
@dataclass(frozen=True)
class ManualDocument:
    title: str
    source_path: str
    content: str
    images: list[str] = field(default_factory=list)


# 表示一段可进入向量库的知识片段，保留来源和图片用于回答时追溯。
@dataclass(frozen=True)
class DocumentChunk:
    id: str
    title: str
    source_path: str
    content: str
    images: list[str] = field(default_factory=list)
