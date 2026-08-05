from decimal import Decimal

from app.evaluation.costs import estimate_deepseek_cost
from app.observability.model_usage import ModelUsageEvent


def test_cost_distinguishes_cache_hits_cache_misses_and_output_tokens():
    cost = estimate_deepseek_cost(
        [ModelUsageEvent("answer", "deepseek-v4-flash", prompt_tokens=1000, completion_tokens=200, cache_hit_tokens=250)],
        {"input_cache_hit_per_million": "1", "input_cache_miss_per_million": "4", "output_per_million": "10"},
    )

    assert cost == Decimal("0.0053")
