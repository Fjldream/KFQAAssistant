from time import perf_counter

from app.evaluation.judge import JudgementCompletion, JudgementError, JudgeProtocol
from app.evaluation.models import MetricResult, MetricStatus
from app.rag.generation.answer_policy import is_no_answer


SYSTEM_PROMPT = """You evaluate a RAG answer. Return only JSON with exact keys:
correctness (number 0..1), relevance (number 0..1), facts (array of {id, covered}),
and forbidden_fact_matches (array of strings). Facts must contain exactly the supplied IDs."""


def _result(name, score, status, threshold=None, details=None, elapsed_ms=0.0, token_usage=None, error_code=None):
    return MetricResult(name, score, status, threshold, details or {}, elapsed_ms, token_usage, error_code)


def _error_results(code: str, elapsed_ms: float) -> list[MetricResult]:
    return [_result(name, None, MetricStatus.ERROR, elapsed_ms=elapsed_ms, error_code=code) for name in (
        "answer_correctness", "answer_relevance", "required_fact_coverage", "forbidden_fact_matches",
    )]


def evaluate_answer_quality(judge: JudgeProtocol, turn, answer: str) -> list[MetricResult]:
    started = perf_counter()
    if not answer.strip() or is_no_answer(answer):
        return [_result(name, None, MetricStatus.SKIPPED, elapsed_ms=(perf_counter() - started) * 1000) for name in (
            "answer_correctness", "answer_relevance", "required_fact_coverage", "forbidden_fact_matches",
        )]
    facts = list(getattr(turn, "required_facts", []))
    fact_payload = [fact.model_dump() if hasattr(fact, "model_dump") else fact for fact in facts]
    try:
        completion = judge.complete_json(
            SYSTEM_PROMPT,
            f"Question: {turn.question}\nReference answer: {getattr(turn, 'reference_answer', '')}\n"
            f"Required facts: {fact_payload}\nForbidden facts: {getattr(turn, 'forbidden_facts', [])}\nAnswer: {answer}",
        )
    except JudgementError:
        return _error_results("judge_http_error", (perf_counter() - started) * 1000)
    data = completion.data if isinstance(completion, JudgementCompletion) else completion
    elapsed_ms = (perf_counter() - started) * 1000
    usage = completion.usage if isinstance(completion, JudgementCompletion) else None
    if not isinstance(data, dict):
        return _error_results("judge_invalid_json", elapsed_ms)
    try:
        correctness, relevance = data["correctness"], data["relevance"]
        returned_facts = data["facts"]
        forbidden = data["forbidden_fact_matches"]
        if (not all(isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1 for value in (correctness, relevance))
                or not isinstance(returned_facts, list) or not isinstance(forbidden, list)):
            raise ValueError
        expected_ids = [str(fact["id"]) for fact in fact_payload]
        fact_by_id = {item["id"]: item for item in returned_facts if isinstance(item, dict) and isinstance(item.get("covered"), bool)}
        if len(fact_by_id) != len(returned_facts) or set(fact_by_id) != set(expected_ids):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        return _error_results("judge_schema_error", elapsed_ms)
    covered_ids = [fact_id for fact_id in expected_ids if fact_by_id[fact_id]["covered"]]
    missing_ids = [fact_id for fact_id in expected_ids if fact_id not in covered_ids]
    coverage = len(covered_ids) / len(expected_ids) if expected_ids else 1.0
    return [
        _result("answer_correctness", float(correctness), MetricStatus.PASSED if correctness >= .8 else MetricStatus.FAILED, .8, elapsed_ms=elapsed_ms, token_usage=usage),
        _result("answer_relevance", float(relevance), MetricStatus.PASSED if relevance >= .8 else MetricStatus.FAILED, .8, elapsed_ms=elapsed_ms, token_usage=usage),
        _result("required_fact_coverage", coverage, MetricStatus.PASSED if coverage >= .8 else MetricStatus.FAILED, .8, {"covered_fact_ids": covered_ids, "missing_fact_ids": missing_ids}, elapsed_ms, usage),
        _result("forbidden_fact_matches", 0.0 if forbidden else 1.0, MetricStatus.FAILED if forbidden else MetricStatus.PASSED, 1.0, {"matches": forbidden}, elapsed_ms, usage),
    ]
