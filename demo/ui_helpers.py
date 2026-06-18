from pathlib import Path
from typing import Any

try:
    from demo.image_paths import resolve_demo_image_path
except ModuleNotFoundError:
    from image_paths import resolve_demo_image_path


DEMO_EXAMPLE_QUESTIONS = [
    "页面编辑器主要包括哪些区域？",
    "如何创建采集工程？",
    "客户端对操作系统有什么要求？",
    "工具栏支持哪些编辑操作？",
]


# 将来源里的 evidence_ids 展示成中文顿号连接的资料编号。
def evidence_label(source: dict[str, Any]) -> str:
    evidence_ids = [str(item) for item in source.get("evidence_ids", []) if item]
    return "、".join(evidence_ids) if evidence_ids else "资料"


# 将检索相似度分数格式化为适合 Demo 展示的短文本。
def score_label(source: dict[str, Any]) -> str:
    score = source.get("score")
    if score is None:
        return "相似度 -"
    return f"相似度 {float(score):.2f}"


# 压缩来源片段里的空白字符并限制长度，避免 Markdown 标题撑大来源卡片。
def snippet_preview(source: dict[str, Any], limit: int = 220) -> str:
    snippet = " ".join(str(source.get("snippet", "")).split())
    if len(snippet) <= limit:
        return snippet
    return f"{snippet[:limit]}..."


# 解析来源图片路径，并保留图片是否存在，方便页面分开展示可用图片和缺失图片。
def resolved_source_images(source: dict[str, Any], data_dir: Path = Path("data/help")) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    for image in source.get("images", []):
        image_path = str(image)
        resolved_path = resolve_demo_image_path(image_path, data_dir=data_dir)
        images.append(
            {
                "path": image_path,
                "resolved_path": resolved_path,
                "exists": resolved_path is not None,
            }
        )
    return images
