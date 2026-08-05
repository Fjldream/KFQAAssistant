import pytest
from app.evaluation.metrics_registry import (
    METRIC_REGISTRY,
    FaithfulnessMetric,
    get_metric,
    list_metrics,
    register_metric,
)
from app.evaluation.judge import JudgeProtocol


class FakeJudge:
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if "拆" in system_prompt:
            return {"claims": ["句1", "句2"]}
        return {"supported": True, "evidence": "依据"}


def test_faithfulness_metric_registered_by_default():
    assert "faithfulness" in METRIC_REGISTRY
    assert isinstance(METRIC_REGISTRY["faithfulness"], FaithfulnessMetric)


def test_faithfulness_metric_evaluate_returns_metric_result():
    result = METRIC_REGISTRY["faithfulness"].evaluate("回答", ["上下文"], FakeJudge())
    assert result.name == "faithfulness"
    assert result.score == 1.0
    assert len(result.details["claims"]) == 2
    assert "elapsed_ms" in result.details


def test_register_and_get_metric_roundtrip():
    class DummyMetric:
        name = "dummy"

        def evaluate(self, answer, contexts, judge):
            return None

    register_metric(DummyMetric())
    try:
        assert get_metric("dummy") is not None
        assert "dummy" in list_metrics()
    finally:
        METRIC_REGISTRY.pop("dummy", None)


def test_register_duplicate_raises():
    with pytest.raises(ValueError):
        register_metric(METRIC_REGISTRY["faithfulness"])


def test_get_metric_unknown_raises_key_error():
    with pytest.raises(KeyError):
        get_metric("unknown")
