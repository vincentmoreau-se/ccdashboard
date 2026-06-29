from __future__ import annotations

import json
import re
from pathlib import Path

from app.models import CostBreakdown, Usage

_MILLION = 1_000_000

# Region prefixes (Bedrock cross-region inference) and version/date suffixes that
# wrap an otherwise-bare model id (e.g. ``us.anthropic.claude-opus-4-8-v1:0`` or
# ``claude-sonnet-4-6-20250514``). pricing.json keys are bare, so we strip these.
_REGION_PREFIX_RE = re.compile(r"^(?:us|eu|apac|global)\.")
_VERSION_SUFFIX_RE = re.compile(r"(?:-v\d+)?:\d+$")
_DATE_SUFFIX_RE = re.compile(r"-\d{8}$")


def detect_provider(model: str | None, default: str) -> str:
    if not model:
        return default
    m = model.lower()
    if m.startswith("us.anthropic.") or m.startswith("eu.anthropic.") or "bedrock" in m:
        return "bedrock"
    return default


def _normalize_model_id(model: str) -> str:
    """Reduce a provider/region/version-decorated model id to its bare pricing key.

    ``us.anthropic.claude-opus-4-8-v1:0`` → ``claude-opus-4-8``;
    ``claude-sonnet-4-6-20250514`` → ``claude-sonnet-4-6``.
    """
    m = _REGION_PREFIX_RE.sub("", model)
    m = m.removeprefix("anthropic.")
    m = _VERSION_SUFFIX_RE.sub("", m)
    m = _DATE_SUFFIX_RE.sub("", m)
    return m


class PriceTable:
    def __init__(self, table: dict[str, dict[str, dict[str, float]]]):
        self._table = table

    @classmethod
    def load(cls, path: Path) -> "PriceTable":
        with open(path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def _prices_for(self, model: str | None, provider: str) -> dict[str, float] | None:
        """Look up a model's prices, trying the exact id then its normalized form."""
        table = self._table.get(provider, {})
        if not model:
            return None
        prices = table.get(model)
        if prices is None:
            prices = table.get(_normalize_model_id(model))
        return prices

    def cost_breakdown_for_usage(
        self, usage: Usage, model: str | None, provider: str
    ) -> CostBreakdown | None:
        """Per-component cost (display currency), or None if the model has no price.

        The two cache-write tiers are collapsed into a single ``cache_write`` bucket
        (what the UI tooltip shows). Summing the four buckets gives the scalar cost.
        """
        prices = self._prices_for(model, provider)
        if prices is None:
            return None
        return CostBreakdown(
            input=usage.input * prices.get("input", 0.0) / _MILLION,
            output=usage.output * prices.get("output", 0.0) / _MILLION,
            cache_write=(
                usage.cache_write_5m * prices.get("cache_write_5m", 0.0)
                + usage.cache_write_1h * prices.get("cache_write_1h", 0.0)
            )
            / _MILLION,
            cache_read=usage.cache_read * prices.get("cache_read", 0.0) / _MILLION,
        )

    def cost_for_usage(
        self, usage: Usage, model: str | None, provider: str
    ) -> tuple[float, bool]:
        bd = self.cost_breakdown_for_usage(usage, model, provider)
        if bd is None:
            return 0.0, False
        return bd.total(), True

    def cache_savings_for_usage(
        self, usage: Usage, model: str | None, provider: str
    ) -> float:
        """Money saved by prompt caching for this usage.

        Cache-read tokens are billed at the cheap cache-read rate instead of the
        full input rate; the saving is the price gap on those tokens. Returns
        ``0.0`` when the model has no price entry (nothing to attribute).
        """
        prices = self._prices_for(model, provider)
        if prices is None:
            return 0.0
        saved_per_token = prices.get("input", 0.0) - prices.get("cache_read", 0.0)
        return usage.cache_read * saved_per_token / _MILLION
