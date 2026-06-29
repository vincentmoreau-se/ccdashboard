from pathlib import Path

from app.models import Usage
from app.pricing import PriceTable, detect_provider

PRICING = Path(__file__).resolve().parents[2] / "pricing.json"


def test_cost_known():
    table = PriceTable.load(PRICING)
    u = Usage(input=1_000_000, output=1_000_000, cache_read=1_000_000)
    cost, known = table.cost_for_usage(u, "claude-opus-4-8", "anthropic")
    assert known is True
    assert cost == 5.0 + 25.0 + 0.5


def test_cost_unknown_model_flagged():
    table = PriceTable.load(PRICING)
    cost, known = table.cost_for_usage(Usage(input=100), "made-up-model", "anthropic")
    assert known is False
    assert cost == 0.0


def test_cache_savings():
    table = PriceTable.load(PRICING)
    # 1M cache-read tokens on opus: input 5.0 vs cache_read 0.5 per million => saved 4.5.
    saved = table.cache_savings_for_usage(
        Usage(cache_read=1_000_000), "claude-opus-4-8", "anthropic"
    )
    assert saved == 4.5


def test_cache_savings_unknown_model_is_zero():
    table = PriceTable.load(PRICING)
    saved = table.cache_savings_for_usage(
        Usage(cache_read=1_000_000), "made-up-model", "anthropic"
    )
    assert saved == 0.0


def test_bedrock_decorated_model_id_matches_bare_price():
    # Cross-region/versioned Bedrock ids must normalize to the bare pricing key.
    table = PriceTable.load(PRICING)
    u = Usage(input=1_000_000, output=1_000_000, cache_read=1_000_000)
    cost, known = table.cost_for_usage(u, "us.anthropic.claude-opus-4-8-v1:0", "bedrock")
    assert known is True
    assert cost == 5.0 + 25.0 + 0.5


def test_anthropic_dated_model_id_matches_bare_price():
    # A dated Anthropic id (e.g. ...-20250514) normalizes to its bare pricing key.
    table = PriceTable.load(PRICING)
    cost, known = table.cost_for_usage(
        Usage(input=1_000_000), "claude-sonnet-4-6-20250514", "anthropic"
    )
    assert known is True
    assert cost == 3.0


def test_detect_provider():
    assert detect_provider("us.anthropic.claude-opus-4-8-v1:0", "anthropic") == "bedrock"
    assert detect_provider("claude-opus-4-8", "anthropic") == "anthropic"
    assert detect_provider(None, "anthropic") == "anthropic"
