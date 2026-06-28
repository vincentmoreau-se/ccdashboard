from pathlib import Path

from app.parser import parse_session_file

FIX = Path(__file__).parent / "fixtures"


def test_parse_sample():
    p = parse_session_file(FIX / "sample.jsonl")
    assert p.session_id == "sess-1"
    assert p.ai_title == "Fix backup loop"
    assert p.skipped_lines == 0
    assistants = [r for r in p.records if r.type == "assistant"]
    assert len(assistants) == 2
    first = assistants[0]
    assert first.model == "claude-opus-4-8"
    assert first.usage.input == 404
    assert first.usage.output == 309
    assert first.usage.cache_read == 16285
    assert first.usage.cache_write_1h == 9665
    assert first.tools == ["Bash"]
    assert set(first.content_kinds) == {"thinking", "tool_use"}


def test_parse_handles_corruption_and_missing_usage():
    p = parse_session_file(FIX / "corrupt.jsonl")
    assert p.skipped_lines == 1  # the "this is not json" line
    a = [r for r in p.records if r.type == "assistant"][0]
    assert a.usage.input == 0  # missing usage -> zeros, no crash
