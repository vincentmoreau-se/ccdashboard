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


def test_detect_provider():
    assert detect_provider("us.anthropic.claude-opus-4-8-v1:0", "anthropic") == "bedrock"
    assert detect_provider("claude-opus-4-8", "anthropic") == "anthropic"
    assert detect_provider(None, "anthropic") == "anthropic"
