# backend/app/evaluation/metrics_registry.py
from app.evaluation.faithfulness import compute_faithfulness
from app.evaluation.judge import JudgeProtocol
from app.evaluation.models import MetricResult, MetricStatus


class Metric:
    name: str

    def evaluate(self, answer: str, contexts: list[str], judge: JudgeProtocol) -> MetricResult:
        ...


class FaithfulnessMetric:
    name = "faithfulness"

    def evaluate(self, answer: str, contexts: list[str], judge: JudgeProtocol) -> MetricResult:
        result = compute_faithfulness(judge, answer, contexts)
        return MetricResult(
            name=self.name,
            score=result.score,
            status=result.status,
            threshold=0.9,
            details={"claims": result.claims, "elapsed_ms": result.elapsed_ms},
            elapsed_ms=result.elapsed_ms,
            token_usage=result.token_usage,
            error_code=result.error_code,
        )


class RegisteredMetric:
    def __init__(self, name: str) -> None:
        self.name = name

    def evaluate(self, answer: str, contexts: list[str], judge: JudgeProtocol) -> MetricResult:
        raise RuntimeError(f"{self.name} must be evaluated with its turn specification")


METRIC_REGISTRY: dict[str, Metric] = {}


def register_metric(metric: Metric) -> None:
    if metric.name in METRIC_REGISTRY:
        raise ValueError(f"指标已注册: {metric.name}")
    METRIC_REGISTRY[metric.name] = metric


def get_metric(name: str) -> Metric:
    return METRIC_REGISTRY[name]


def list_metrics() -> list[str]:
    return list(METRIC_REGISTRY)


register_metric(FaithfulnessMetric())
for _name in (
    "answer_correctness", "answer_relevance", "required_fact_coverage", "forbidden_fact_matches",
    "hit_at_k", "recall_at_k", "mrr", "chunk_hit_at_k", "forbidden_source_matches",
):
    register_metric(RegisteredMetric(_name))
