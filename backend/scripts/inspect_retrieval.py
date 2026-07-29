import argparse

from app.rag.factory import create_vector_store
from app.rag.retriever import RetrievedChunk, RetrieverService
from app.rag.vector_store import combined_score, keyword_score


# 截取片段预览，避免调试输出被长文本淹没。
def _snippet(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact[:limit]


# 将检索结果格式化为命令行可读报告，方便分析命中来源和分数。
def format_retrieval_results(query: str, results: list[RetrievedChunk]) -> str:
    lines = [f"查询: {query}", f"命中数量: {len(results)}", ""]
    for index, item in enumerate(results, start=1):
        chunk = item.chunk
        vector_score = item.score if item.score is not None else 0.0
        keyword = keyword_score(query, chunk)
        lines.extend(
            [
                f"Rank {index}",
                f"  向量分: {vector_score:.2f}",
                f"  关键词分: {keyword:.2f}",
                f"  综合分: {combined_score(query, item):.2f}",
                f"  标题: {chunk.title}",
                f"  来源: {chunk.source_path}",
                f"  图片: {', '.join(chunk.images) or '无'}",
                f"  片段: {_snippet(chunk.content)}",
                "",
            ]
        )
    return "\n".join(lines)


# 命令行入口：只运行检索，不调用大模型，用于定位 RAG 是否先找对了资料。
def main() -> None:
    parser = argparse.ArgumentParser(description="检查某个问题的 RAG 检索命中结果")
    parser.add_argument("question", help="要检查的用户问题")
    parser.add_argument("--top-k", type=int, default=5, help="返回的检索结果数量")
    args = parser.parse_args()

    retriever = RetrieverService(create_vector_store(), top_k=args.top_k)
    results = retriever.retrieve(args.question)
    print(format_retrieval_results(args.question, results))


if __name__ == "__main__":
    main()
