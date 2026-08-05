from app.evaluation.models import MetricResult, MetricStatus


def _result(name, score, status, threshold=None, details=None, error_code=None):
    return MetricResult(name, score, status, threshold, details or {}, error_code=error_code)


def evaluate_retrieval(turn, sources) -> list[MetricResult]:
    expected_sources = list(getattr(turn, "expected_source_ids", []))
    expected_chunks = list(getattr(turn, "expected_chunk_ids", []))
    forbidden_sources = list(getattr(turn, "forbidden_source_ids", []))
    actual_sources = [source.source_id for source in sources]
    actual_chunks = [chunk_id for source in sources for chunk_id in source.chunk_ids]
    results = []
    if expected_sources and any(source_id is None for source_id in actual_sources):
        results.extend([_result(name, None, MetricStatus.ERROR, error_code="missing_source_ids") for name in ("hit_at_k", "recall_at_k", "mrr")])
    elif expected_sources:
        matched = [source_id for source_id in expected_sources if source_id in actual_sources]
        first_rank = next((index + 1 for index, source_id in enumerate(actual_sources) if source_id in expected_sources), None)
        results.extend([
            _result("hit_at_k", 1.0 if matched else 0.0, MetricStatus.PASSED if matched else MetricStatus.FAILED, 1.0, {"matched_source_ids": matched}),
            _result("recall_at_k", len(matched) / len(expected_sources), MetricStatus.PASSED if len(matched) == len(expected_sources) else MetricStatus.FAILED, 1.0, {"matched_source_ids": matched}),
            _result("mrr", 1.0 / first_rank if first_rank else 0.0, MetricStatus.PASSED if first_rank else MetricStatus.FAILED, 1.0),
        ])
    if expected_chunks:
        matched_chunks = [chunk_id for chunk_id in expected_chunks if chunk_id in actual_chunks]
        results.append(_result("chunk_hit_at_k", 1.0 if matched_chunks else 0.0, MetricStatus.PASSED if matched_chunks else MetricStatus.FAILED, 1.0, {"matched_chunk_ids": matched_chunks}))
    if forbidden_sources:
        matched_forbidden = [source_id for source_id in forbidden_sources if source_id in actual_sources]
        results.append(_result("forbidden_source_matches", 0.0 if matched_forbidden else 1.0, MetricStatus.FAILED if matched_forbidden else MetricStatus.PASSED, 1.0, {"matched_source_ids": matched_forbidden}))
    return results
