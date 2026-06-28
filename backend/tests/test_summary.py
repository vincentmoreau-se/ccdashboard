import json
from pathlib import Path

from app.parser import parse_lines, parse_session_file
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


def test_provider_from_first_assistant_model():
    # First assistant uses an anthropic model; a later one uses a us.anthropic.*
    # (bedrock) model. Provider must be derived from the FIRST, so it stays "anthropic".
    lines = [
        json.dumps(
            {
                "type": "assistant",
                "uuid": "a1",
                "sessionId": "sess-x",
                "timestamp": "2026-06-11T17:00:00.000Z",
                "message": {"model": "claude-opus-4-8", "content": [{"type": "text"}]},
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "uuid": "a2",
                "parentUuid": "a1",
                "sessionId": "sess-x",
                "timestamp": "2026-06-11T17:01:00.000Z",
                "message": {
                    "model": "us.anthropic.claude-opus-4-8",
                    "content": [{"type": "text"}],
                },
            }
        ),
    ]
    parsed = parse_lines(lines)
    s = summarize_session(
        parsed,
        file_path=Path("inmemory.jsonl"),
        project="p",
        table=PriceTable({}),
        default_provider="anthropic",
        active_threshold_seconds=30,
        now_ts=1_000_000.0,
        mtime=1_000_000.0,
    )
    assert s.provider == "anthropic"
    assert s.models == ["claude-opus-4-8", "us.anthropic.claude-opus-4-8"]


def test_unknown_model_sets_cost_known_false():
    parsed = parse_session_file(FIX / "corrupt.jsonl")
    # Empty price table makes every (provider, model) lookup unknown.
    empty = PriceTable({})
    s = summarize_session(
        parsed, file_path=FIX / "corrupt.jsonl", project="p",
        table=empty, default_provider="anthropic",
        active_threshold_seconds=30, now_ts=2_000_000.0, mtime=0.0,
    )
    assert s.cost_known is False
    assert s.is_active is False
