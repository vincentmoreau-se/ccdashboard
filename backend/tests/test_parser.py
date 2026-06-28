import json
from pathlib import Path

from app.parser import parse_lines, parse_session_file

FIX = Path(__file__).parent / "fixtures"


def _assistant_line(*tool_uses) -> str:
    content = [{"type": "tool_use", "name": n, "input": i} for n, i in tool_uses]
    return json.dumps(
        {"type": "assistant", "sessionId": "s", "message": {"model": "claude-opus-4-8", "content": content}}
    )


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


def test_lines_generated_per_write_class_tool():
    line = _assistant_line(
        ("Write", {"content": "a\nb\nc"}),                       # 3
        ("Edit", {"old_string": "1\n2\n3\n4", "new_string": "x\ny"}),  # 2, old ignored
        ("MultiEdit", {"edits": [{"new_string": "1\n2"}, {"new_string": "3"}]}),  # 3
        ("NotebookEdit", {"new_source": "p\nq\nr\ns"}),          # 4
        ("Bash", {"command": "ls\n-la"}),                        # 0 (not a write tool)
    )
    rec = parse_lines([line]).records[0]
    assert rec.lines_generated == 3 + 2 + 3 + 4


def test_lines_generated_defaults_zero_without_write_tools():
    p = parse_session_file(FIX / "sample.jsonl")
    assert all(r.lines_generated == 0 for r in p.records)  # sample has only Bash


def test_parse_handles_corruption_and_missing_usage():
    p = parse_session_file(FIX / "corrupt.jsonl")
    assert p.skipped_lines == 1  # the "this is not json" line
    a = [r for r in p.records if r.type == "assistant"][0]
    assert a.usage.input == 0  # missing usage -> zeros, no crash
