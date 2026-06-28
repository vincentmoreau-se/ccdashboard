from __future__ import annotations

import json
from pathlib import Path

from app.models import Usage

_MILLION = 1_000_000


def detect_provider(model: str | None, default: str) -> str:
    if not model:
        return default
    m = model.lower()
    if m.startswith("us.anthropic.") or m.startswith("eu.anthropic.") or "bedrock" in m:
        return "bedrock"
    return default


class PriceTable:
    def __init__(self, table: dict[str, dict[str, dict[str, float]]]):
        self._table = table

    @classmethod
    def load(cls, path: Path) -> "PriceTable":
        with open(path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def cost_for_usage(
        self, usage: Usage, model: str | None, provider: str
    ) -> tuple[float, bool]:
        prices = self._table.get(provider, {}).get(model or "")
        if prices is None:
            return 0.0, False
        cost = (
            usage.input * prices.get("input", 0.0)
            + usage.output * prices.get("output", 0.0)
            + usage.cache_write_5m * prices.get("cache_write_5m", 0.0)
            + usage.cache_write_1h * prices.get("cache_write_1h", 0.0)
            + usage.cache_read * prices.get("cache_read", 0.0)
        ) / _MILLION
        return cost, True

    def cache_savings_for_usage(
        self, usage: Usage, model: str | None, provider: str
    ) -> float:
        """Money saved by prompt caching for this usage.

        Cache-read tokens are billed at the cheap cache-read rate instead of the
        full input rate; the saving is the price gap on those tokens. Returns
        ``0.0`` when the model has no price entry (nothing to attribute).
        """
        prices = self._table.get(provider, {}).get(model or "")
        if prices is None:
            return 0.0
        saved_per_token = prices.get("input", 0.0) - prices.get("cache_read", 0.0)
        return usage.cache_read * saved_per_token / _MILLION
