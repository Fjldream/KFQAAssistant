from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field


DEEPSEEK_FLASH_MODEL = "deepseek-v4-flash"


@dataclass(frozen=True)
class ModelUsageEvent:
    operation: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cache_hit_tokens: int = 0


@dataclass
class ModelUsageCollector:
    events: list[ModelUsageEvent] = field(default_factory=list)


_collector: ContextVar[ModelUsageCollector | None] = ContextVar("model_usage_collector", default=None)


@contextmanager
def capture_model_usage() -> Iterator[ModelUsageCollector]:
    collector = ModelUsageCollector()
    token = _collector.set(collector)
    try:
        yield collector
    finally:
        _collector.reset(token)


def _usage_value(usage: Mapping[str, object], field: str) -> int:
    value = usage.get(field, 0)
    return value if isinstance(value, int) else 0


def usage_event_from_response(operation: str, model: str, response: Mapping[str, object]) -> ModelUsageEvent:
    usage = response.get("usage", {})
    usage_data = usage if isinstance(usage, Mapping) else {}
    return ModelUsageEvent(
        operation=operation,
        model=model,
        prompt_tokens=_usage_value(usage_data, "prompt_tokens"),
        completion_tokens=_usage_value(usage_data, "completion_tokens"),
        cache_hit_tokens=_usage_value(usage_data, "prompt_cache_hit_tokens"),
    )


def record_model_usage(
    operation: str,
    model: str,
    usage: Mapping[str, object] | None = None,
) -> ModelUsageEvent:
    event = usage_event_from_response(operation, model, {"usage": usage or {}})
    collector = _collector.get()
    if collector is not None:
        collector.events.append(event)
    return event
