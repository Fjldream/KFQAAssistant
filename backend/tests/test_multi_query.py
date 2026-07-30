from app.rag.models import DocumentChunk
from app.rag.retrieval.multi_query import merge_retrieved_candidates
from app.rag.retrieval.retriever import RetrievedChunk


def test_merge_retrieved_candidates_deduplicates_by_chunk_id():
    first = RetrievedChunk(DocumentChunk(id="a::0", title="A", source_path="a.md", content="创建工程"), score=0.7)
    duplicate = RetrievedChunk(DocumentChunk(id="a::0", title="A", source_path="a.md", content="创建工程"), score=0.9)
    second = RetrievedChunk(DocumentChunk(id="b::0", title="B", source_path="b.md", content="启动工程"), score=0.8)

    merged = merge_retrieved_candidates({"q1": [first], "q2": [duplicate, second]}, limit=10)

    assert [item.chunk.id for item in merged] == ["a::0", "b::0"]
    assert merged[0].score == 0.9


def test_merge_retrieved_candidates_prefers_high_rank_hits_across_queries():
    top_ranked = RetrievedChunk(DocumentChunk(id="a::0", title="A", source_path="a.md", content="创建工程"), score=0.95)
    lower_ranked = RetrievedChunk(DocumentChunk(id="b::0", title="B", source_path="b.md", content="启动工程"), score=0.95)

    merged = merge_retrieved_candidates({"q1": [top_ranked, lower_ranked]}, limit=10)

    assert [item.chunk.id for item in merged] == ["a::0", "b::0"]
