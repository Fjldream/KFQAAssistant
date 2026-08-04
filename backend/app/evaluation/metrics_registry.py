# backend/app/evaluation/metrics_registry.py
from dataclasses import dataclass, field

from app.evaluation.faithfulness import compute_faithfulness
from app.evaluation.judge import JudgeProtocol


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float | None
    details: dict = field(default_factory=dict)


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
            details={"claims": result.claims, "elapsed_ms": result.elapsed_ms},
        )


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
