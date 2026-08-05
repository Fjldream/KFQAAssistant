from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Sequence

from app.observability.model_usage import ModelUsageEvent


def estimate_deepseek_cost(events: Sequence[ModelUsageEvent], rates: Mapping[str, object]) -> Decimal:
    """Estimate RMB cost from the DeepSeek usage fields captured for a run."""
    cache_hit_rate = Decimal(str(rates.get("input_cache_hit_per_million", 0)))
    cache_miss_rate = Decimal(str(rates.get("input_cache_miss_per_million", 0)))
    output_rate = Decimal(str(rates.get("output_per_million", 0)))
    cache_hits = sum(event.cache_hit_tokens for event in events)
    prompt_tokens = sum(event.prompt_tokens for event in events)
    output_tokens = sum(event.completion_tokens for event in events)
    cache_misses = max(0, prompt_tokens - cache_hits)
    total = (
        Decimal(cache_hits) * cache_hit_rate
        + Decimal(cache_misses) * cache_miss_rate
        + Decimal(output_tokens) * output_rate
    ) / Decimal("1000000")
    return total.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
