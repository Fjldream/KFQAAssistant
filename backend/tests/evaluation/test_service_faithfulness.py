from app.evaluation.models import CaseResult, TurnResult
from app.evaluation.service import EvaluationService


def _service() -> EvaluationService:
    return EvaluationService.__new__(EvaluationService)  # 只测转换，不触发 __init__


def test_turn_result_from_payload_passes_faithfulness():
    service = _service()
    payload = {
        "question": "q", "answer": "a", "standalone_question": None, "passed": True,
        "keyword_passed": True, "source_passed": True, "image_passed": True, "no_answer_passed": True,
        "faithfulness_score": 0.4,
        "faithfulness_claims": [{"claim": "句1", "supported": False, "evidence": ""}],
        "faithfulness_elapsed_ms": 55.0,
    }
    turn = service.turn_result_from_payload(payload)
    assert turn.faithfulness_score == 0.4
    assert turn.faithfulness_claims[0]["supported"] is False
    assert turn.faithfulness_elapsed_ms == 55.0


def test_turn_result_from_payload_defaults_when_missing():
    service = _service()
    payload = {
        "question": "q", "answer": "a", "standalone_question": None, "passed": True,
        "keyword_passed": True, "source_passed": True, "image_passed": True, "no_answer_passed": True,
    }
    turn = service.turn_result_from_payload(payload)
    assert turn.faithfulness_score is None
    assert turn.faithfulness_claims == []
