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
    # The per-component breakdown must sum back to the scalar cost.
    assert abs(s.cost_breakdown.total() - s.cost) < 1e-12
    assert s.cost_breakdown.cache_read > 0  # sample has cache_read on opus
    # sample.jsonl has cache_read=16285 on opus -> real savings; and content kinds.
    assert s.cache_savings > 0
    assert s.content_kind_counts.get("thinking", 0) >= 1
    assert s.content_kind_counts.get("tool_use", 0) >= 1


def test_usage_deduplicated_per_message_id():
    # Claude Code writes one assistant response across several lines that share the
    # same message.id and repeat the identical message.usage (one line per content
    # block). Usage/cost must be counted ONCE per message.id, but per-block signals
    # (tools, lines) stay counted per line.
    usage = {"input_tokens": 100, "output_tokens": 10}
    lines = [
        json.dumps({
            "type": "assistant", "uuid": "u1", "sessionId": "sd",
            "timestamp": "2026-06-11T17:00:00.000Z",
            "message": {"id": "msg_1", "model": "claude-opus-4-8", "usage": usage,
                        "content": [{"type": "text", "text": "hi"}]},
        }),
        json.dumps({
            "type": "assistant", "uuid": "u2", "sessionId": "sd",
            "timestamp": "2026-06-11T17:00:01.000Z",
            "message": {"id": "msg_1", "model": "claude-opus-4-8", "usage": usage,
                        "content": [{"type": "tool_use", "name": "Bash", "input": {}}]},
        }),
        json.dumps({
            "type": "assistant", "uuid": "u3", "sessionId": "sd",
            "timestamp": "2026-06-11T17:00:02.000Z",
            "message": {"id": "msg_2", "model": "claude-opus-4-8",
                        "usage": {"input_tokens": 50, "output_tokens": 5},
                        "content": [{"type": "tool_use", "name": "Bash", "input": {}}]},
        }),
    ]
    table = PriceTable.load(PRICING)
    s = summarize_session(
        parse_lines(lines), file_path=Path("inmemory.jsonl"), project="p",
        table=table, default_provider="anthropic",
        active_threshold_seconds=30, now_ts=1_000_000.0, mtime=1_000_000.0,
    )
    # msg_1 usage counted once (100+50 input, not 200+50); per-block tools still 2.
    assert s.usage.input == 150
    assert s.usage.output == 15
    assert s.tool_counts == {"Bash": 2}
    # Cost = deduped usage priced on opus (input 5.0/M, output 25.0/M).
    expected = (150 * 5.0 + 15 * 25.0) / 1_000_000
    assert abs(s.cost - expected) < 1e-12


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


# ---------------------------------------------------------------------------
# B1: technology/tooling signal folding
# ---------------------------------------------------------------------------

def _make_session(lines, **kw):
    return summarize_session(
        parse_lines(lines), file_path=Path("x.jsonl"), project="p",
        table=PriceTable({}), default_provider="anthropic",
        active_threshold_seconds=30, now_ts=1_000_000.0, mtime=1_000_000.0,
        **kw,
    )


def test_builtin_vs_user_tool_split():
    """Built-in tools go to builtin_tool_counts; MCP and Skill go to user_tool_counts."""
    lines = [
        json.dumps({
            "type": "assistant", "sessionId": "s",
            "timestamp": "2026-06-28T10:00:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Bash", "input": {}},
                {"type": "tool_use", "name": "Write", "input": {}},
                {"type": "tool_use", "name": "Edit", "input": {}},
                {"type": "tool_use", "name": "Skill", "input": {"skill": "test-skill"}},
                {"type": "tool_use", "name": "mcp__playwright__browser_navigate", "input": {}},
            ]},
        }),
    ]
    s = _make_session(lines)
    # Builtins
    assert s.builtin_tool_counts.get("Bash") == 1
    assert s.builtin_tool_counts.get("Write") == 1
    assert s.builtin_tool_counts.get("Edit") == 1
    # User tools
    assert s.user_tool_counts.get("Skill") == 1
    assert s.user_tool_counts.get("mcp__playwright__browser_navigate") == 1
    # Cross-check: no bleed between the two maps
    assert "Bash" not in s.user_tool_counts
    assert "Write" not in s.user_tool_counts
    assert "Edit" not in s.user_tool_counts
    assert "Skill" not in s.builtin_tool_counts
    assert "mcp__playwright__browser_navigate" not in s.builtin_tool_counts


def test_builtin_split_agent_is_builtin():
    """Agent is a built-in tool even though it spawns subagents."""
    lines = [
        json.dumps({
            "type": "assistant", "sessionId": "s",
            "timestamp": "2026-06-28T10:00:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "Explore"}},
            ]},
        }),
    ]
    s = _make_session(lines)
    assert s.builtin_tool_counts.get("Agent") == 1
    assert "Agent" not in s.user_tool_counts


def test_language_counts_fold():
    """Language occurrences across records are counted in language_counts."""
    lines = [
        json.dumps({
            "type": "assistant", "sessionId": "s",
            "timestamp": "2026-06-28T10:00:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/src/a.py", "content": "pass"}},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/src/b.py", "content": "pass"}},
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "/src/App.tsx", "old_string": "x", "new_string": "y"}},
            ]},
        }),
    ]
    s = _make_session(lines)
    assert s.language_counts.get("Python") == 2
    assert s.language_counts.get("TypeScript/React") == 1


def test_framework_counts_fold():
    """Framework occurrences across records are counted in framework_counts."""
    lines = [
        json.dumps({
            "type": "assistant", "sessionId": "s",
            "timestamp": "2026-06-28T10:00:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": "uv run pytest"}},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/app/package.json", "content": "{}"}},
            ]},
        }),
    ]
    s = _make_session(lines)
    assert s.framework_counts.get("Python") >= 1   # from uv
    assert s.framework_counts.get("pytest") >= 1   # from pytest
    assert s.framework_counts.get("Node.js") >= 1  # from package.json


def test_skill_mcp_subagent_slash_counts():
    """Skill, MCP server, subagent, and slash command counts are folded correctly."""
    lines = [
        json.dumps({
            "type": "assistant", "sessionId": "s",
            "timestamp": "2026-06-28T10:00:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Skill", "input": {"skill": "deploy-nas"}},
                {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "Explore"}},
                {"type": "tool_use", "name": "mcp__playwright__browser_navigate", "input": {}},
            ]},
        }),
        json.dumps({
            "type": "user", "sessionId": "s",
            "timestamp": "2026-06-28T10:01:00.000Z",
            "message": {"role": "user", "content": "<command-name>/clear</command-name>"},
        }),
    ]
    s = _make_session(lines)
    assert s.skill_counts == {"deploy-nas": 1}
    assert s.subagent_counts == {"Explore": 1}
    assert s.mcp_server_counts == {"playwright": 1}
    assert s.slash_command_counts == {"/clear": 1}


def test_counts_accumulate_across_records():
    """Counts from multiple records in a session are summed together."""
    lines = [
        json.dumps({
            "type": "assistant", "sessionId": "s",
            "timestamp": "2026-06-28T10:00:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/a.py", "content": "x"}},
            ]},
        }),
        json.dumps({
            "type": "assistant", "sessionId": "s",
            "timestamp": "2026-06-28T10:01:00.000Z",
            "message": {"model": "claude-opus-4-8", "content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/b.py", "content": "y"}},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/c.py", "content": "z"}},
            ]},
        }),
    ]
    s = _make_session(lines)
    assert s.language_counts.get("Python") == 3
    assert s.builtin_tool_counts.get("Write") == 3
