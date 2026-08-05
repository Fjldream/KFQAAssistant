from app.evaluation.models import MetricStatus
from app.evaluation.retrieval_metrics import evaluate_retrieval
from app.evaluation.suite import EvaluationTurnSpec
from app.schemas.chat import SourceSnippet


def turn_spec(**kwargs):
    return EvaluationTurnSpec(question="问题？", **kwargs)


def sources(*source_ids):
    return [
        SourceSnippet(title=source_id, source_path=f"{source_id}.md", snippet="内容", source_id=source_id)
        for source_id in source_ids
    ]


def metric_by_name(results, name):
    return next(result for result in results if result.name == name)


def test_retrieval_metrics_use_source_ids_not_keywords():
    results = evaluate_retrieval(turn_spec(expected_source_ids=["doc-a", "doc-b"]), sources("doc-x", "doc-b"))

    assert metric_by_name(results, "hit_at_k").score == 1.0
    assert metric_by_name(results, "recall_at_k").score == 0.5
    assert metric_by_name(results, "mrr").score == 0.5


def test_retrieval_reports_forbidden_source_match():
    results = evaluate_retrieval(turn_spec(forbidden_source_ids=["doc-b"]), sources("doc-b"))

    forbidden = metric_by_name(results, "forbidden_source_matches")
    assert forbidden.score == 0.0
    assert forbidden.status == MetricStatus.FAILED
    assert forbidden.details["matched_source_ids"] == ["doc-b"]


def test_retrieval_matches_expected_chunk_ids_exactly():
    results = evaluate_retrieval(
        turn_spec(expected_chunk_ids=["chunk-a"]),
        [SourceSnippet(title="t", source_path="t.md", snippet="chunk-a", source_id="doc-a", chunk_ids=["chunk-x"])],
    )

    chunks = metric_by_name(results, "chunk_hit_at_k")
    assert chunks.score == 0.0
    assert chunks.status == MetricStatus.FAILED


def test_retrieval_returns_error_when_identifiers_are_missing():
    results = evaluate_retrieval(turn_spec(expected_source_ids=["doc-a"]), [SourceSnippet(title="t", source_path="t.md", snippet="内容")])

    assert metric_by_name(results, "hit_at_k").status == MetricStatus.ERROR
    assert metric_by_name(results, "hit_at_k").error_code == "missing_source_ids"


def test_retrieval_returns_skipped_results_when_metric_is_not_applicable():
    results = evaluate_retrieval(turn_spec(), sources("doc-a"))

    assert {result.name for result in results} == {"hit_at_k", "recall_at_k", "mrr", "chunk_hit_at_k", "forbidden_source_matches"}
    assert {result.status for result in results} == {MetricStatus.SKIPPED}
