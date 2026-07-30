from app.rag.retriever import RetrievedChunk


# 合并多条查询的召回结果，同一 chunk 只保留最高相关性版本。
def merge_retrieved_candidates(results_by_query: dict[str, list[RetrievedChunk]], limit: int) -> list[RetrievedChunk]:
    best_by_id: dict[str, RetrievedChunk] = {}
    best_merge_score_by_id: dict[str, float] = {}
    first_seen_order: dict[str, int] = {}
    order = 0
    for results in results_by_query.values():
        for rank, item in enumerate(results):
            chunk_id = item.chunk.id
            if chunk_id not in first_seen_order:
                first_seen_order[chunk_id] = order
                order += 1
            item_score = item.score if item.score is not None else float("-inf")
            rank_bonus = 1.0 / (rank + 1) * 0.001
            merge_score = item_score + rank_bonus
            if chunk_id not in best_by_id or merge_score > best_merge_score_by_id[chunk_id]:
                best_by_id[chunk_id] = item
                best_merge_score_by_id[chunk_id] = merge_score

    ranked = sorted(
        best_by_id.values(),
        key=lambda item: (best_merge_score_by_id[item.chunk.id], -first_seen_order[item.chunk.id]),
        reverse=True,
    )
    return ranked[:limit]
