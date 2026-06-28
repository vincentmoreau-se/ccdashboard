from pathlib import Path

from app.parser import parse_session_file
from app.pricing import PriceTable
from app.summary import summarize_session

FIX = Path(__file__).parent / "fixtures"
PRICING = Path(__file__).resolve().parents[2] / "pricing.json"


def test_summarize_sample():
    parsed = parse_session_file(FIX / "sample.jsonl")
    table = PriceTable.load(PRICING)
    s = summarize_session(
        parsed,
        file_path=FIX / "sample.jsonl",
        project="-home-vemore-workspace-countscore",
        table=table,
        default_provider="anthropic",
        active_threshold_seconds=30,
        now_ts=1_000_000.0,
        mtime=999_990.0,  # 10s ago -> active
    )
    assert s.session_id == "sess-1"
    assert s.ai_title == "Fix backup loop"
    assert s.message_count == 3  # 1 user + 2 assistant records
    assert s.models == ["claude-opus-4-8"]
    assert s.provider == "anthropic"
    assert s.usage.input == 414  # 404 + 10
    assert s.tool_counts == {"Bash": 1}
    assert s.is_active is True
    assert s.cost_known is True
    assert s.cost > 0


def test_unknown_model_sets_cost_known_false():
    parsed = parse_session_file(FIX / "corrupt.jsonl")
    table = PriceTable.load(PRICING)  # haiku exists, so make it unknown by empty table
    empty = PriceTable({})
    s = summarize_session(
        parsed, file_path=FIX / "corrupt.jsonl", project="p",
        table=empty, default_provider="anthropic",
        active_threshold_seconds=30, now_ts=2_000_000.0, mtime=0.0,
    )
    assert s.cost_known is False
    assert s.is_active is False
