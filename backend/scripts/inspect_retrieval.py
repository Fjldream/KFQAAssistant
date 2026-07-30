import argparse

from app.core.config import get_settings
from app.rag.factory import create_vector_store
from app.rag.multi_query import merge_retrieved_candidates
from app.rag.query_rewriter import DeepSeekQueryRewriter, QueryRewriterProtocol
from app.rag.reranker import explain_rerank, rerank
from app.rag.retriever import RetrievedChunk
from app.rag.vector_store import combined_score, keyword_score


# 截取片段预览，避免调试输出被长文本淹没。
def _snippet(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact[:limit]


# 将检索结果格式化为命令行可读报告，方便分析命中来源和分数。
def format_retrieval_results(
    query: str,
    results: list[RetrievedChunk],
    rewritten_queries: list[str] | None = None,
) -> str:
    lines = [f"查询: {query}", f"命中数量: {len(results)}", ""]
    if rewritten_queries:
        lines.append("改写查询:")
        lines.extend(f"  {index}. {item}" for index, item in enumerate(rewritten_queries, start=1))
        lines.append("")
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
                f"  重排原因: {', '.join(explain_rerank(query, item)) or '无'}",
                f"  标题: {chunk.title}",
                f"  来源: {chunk.source_path}",
                f"  图片: {', '.join(chunk.images) or '无'}",
                f"  片段: {_snippet(chunk.content)}",
                "",
            ]
        )
    return "\n".join(lines)


# 根据当前配置创建查询改写器，调试脚本用它展示真实改写查询。
def _create_query_rewriter(enabled: bool) -> QueryRewriterProtocol | None:
    if not enabled:
        return None
    settings = get_settings()
    if not settings.enable_query_rewrite:
        return None
    return DeepSeekQueryRewriter(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout_seconds=settings.deepseek_timeout_seconds,
        max_queries=settings.query_rewrite_max_queries,
    )


# 执行调试检索，支持展示 Query Rewrite 后的多路召回结果。
def inspect_retrieval(question: str, top_k: int, rewrite_enabled: bool = True) -> tuple[list[RetrievedChunk], list[str] | None]:
    vector_store = create_vector_store()
    query_rewriter = _create_query_rewriter(rewrite_enabled)
    if query_rewriter is None:
        candidates = vector_store.similarity_search(question, top_k)
        return rerank(question, candidates, top_k), None

    rewrite_result = query_rewriter.rewrite(question)
    results_by_query = {
        rewritten_query: vector_store.similarity_search(rewritten_query, top_k)
        for rewritten_query in rewrite_result.queries
    }
    candidates = merge_retrieved_candidates(results_by_query, limit=max(top_k * len(rewrite_result.queries), top_k))
    return rerank(question, candidates, top_k), rewrite_result.queries


# 命令行入口：只运行检索，不调用大模型，用于定位 RAG 是否先找对了资料。
def main() -> None:
    parser = argparse.ArgumentParser(description="检查某个问题的 RAG 检索命中结果")
    parser.add_argument("question", help="要检查的用户问题")
    parser.add_argument("--top-k", type=int, default=5, help="返回的检索结果数量")
    parser.add_argument("--no-rewrite", action="store_true", help="关闭 Query Rewrite，只使用原始问题检索")
    args = parser.parse_args()

    results, rewritten_queries = inspect_retrieval(args.question, args.top_k, rewrite_enabled=not args.no_rewrite)
    print(format_retrieval_results(args.question, results, rewritten_queries=rewritten_queries))


if __name__ == "__main__":
    main()
