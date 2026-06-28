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
    # sample.jsonl has cache_read=16285 on opus -> real savings; and content kinds.
    assert s.cache_savings > 0
    assert s.content_kind_counts.get("thinking", 0) >= 1
    assert s.content_kind_counts.get("tool_use", 0) >= 1


def test_lines_generated_accumulates_per_session():
    lines = [
        json.dumps({
            "type": "assistant", "sessionId": "sl", "timestamp": "2026-06-11T17:00:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Write", "input": {"content": "a\nb\nc"}},
            ]},
        }),
        json.dumps({
            "type": "assistant", "sessionId": "sl", "timestamp": "2026-06-11T17:01:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Edit", "input": {"new_string": "x\ny"}},
            ]},
        }),
    ]
    s = summarize_session(
        parse_lines(lines), file_path=Path("inmemory.jsonl"), project="p",
        table=PriceTable({}), default_provider="anthropic",
        active_threshold_seconds=30, now_ts=1_000_000.0, mtime=1_000_000.0,
    )
    assert s.lines_generated == 5  # 3 + 2


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


def test_synthetic_placeholder_model_keeps_cost_known():
    # Claude Code writes assistant turns with model "<synthetic>" (local commands,
    # compaction notices). They carry zero usage and have no price; they must NOT
    # flip cost_known to False, nor appear among the real models.
    lines = [
        json.dumps(
            {
                "type": "assistant",
                "uuid": "a1",
                "sessionId": "sess-s",
                "timestamp": "2026-06-11T17:00:00.000Z",
                "message": {
                    "model": "claude-opus-4-8",
                    "content": [{"type": "text"}],
                    "usage": {"input_tokens": 100, "output_tokens": 10},
                },
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "uuid": "a2",
                "parentUuid": "a1",
                "sessionId": "sess-s",
                "timestamp": "2026-06-11T17:01:00.000Z",
                "message": {"model": "<synthetic>", "content": [{"type": "text"}]},
            }
        ),
    ]
    parsed = parse_lines(lines)
    table = PriceTable.load(PRICING)
    s = summarize_session(
        parsed, file_path=Path("inmemory.jsonl"), project="p",
        table=table, default_provider="anthropic",
        active_threshold_seconds=30, now_ts=1_000_000.0, mtime=1_000_000.0,
    )
    assert s.cost_known is True
    assert s.models == ["claude-opus-4-8"]  # "<synthetic>" excluded
    assert s.cost > 0


def test_only_synthetic_model_is_cost_known_and_zero():
    # A session containing only synthetic assistant turns has a fully-known cost of 0.
    lines = [
        json.dumps(
            {
                "type": "assistant",
                "uuid": "a1",
                "sessionId": "sess-only",
                "timestamp": "2026-06-11T17:00:00.000Z",
                "message": {"model": "<synthetic>", "content": [{"type": "text"}]},
            }
        ),
    ]
    parsed = parse_lines(lines)
    s = summarize_session(
        parsed, file_path=Path("inmemory.jsonl"), project="p",
        table=PriceTable({}), default_provider="anthropic",
        active_threshold_seconds=30, now_ts=1_000_000.0, mtime=1_000_000.0,
    )
    assert s.cost_known is True
    assert s.cost == 0.0
    assert s.models == []


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
