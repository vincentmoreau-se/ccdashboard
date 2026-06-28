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


# ---------------------------------------------------------------------------
# B1: technology/tooling signal extraction
# ---------------------------------------------------------------------------

def test_language_extraction():
    """Languages are extracted from file_path of Write/Edit tools."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/src/main.py", "content": "pass"}},
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/src/App.tsx", "old_string": "x", "new_string": "y"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.languages == ["Python", "TypeScript/React"]


def test_framework_from_manifest():
    """Node.js framework is detected from package.json file path."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/app/package.json", "content": "{}"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert "Node.js" in rec.frameworks
    # package.json is also .json → JSON language
    assert "JSON" in rec.languages


def test_framework_from_bash_command():
    """Frameworks are extracted from Bash command tokens."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "uv run pytest"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert "Python" in rec.frameworks
    assert "pytest" in rec.frameworks


def test_framework_from_bash_deduplicates():
    """frameworks_for_command deduplicates within one command."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "npm install && npm run build"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.frameworks.count("Node.js") == 1


def test_skill_extraction():
    """Skill names are extracted from Skill tool input."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "superpowers:writing-plans"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.skills == ["superpowers:writing-plans"]


def test_subagent_extraction_agent():
    """Subagent types are extracted from Agent tool input."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "Explore"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.subagents == ["Explore"]


def test_subagent_extraction_task():
    """Subagent types are extracted from Task tool input."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "Task", "input": {"subagent_type": "Plan"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.subagents == ["Plan"]


def test_mcp_server_extraction():
    """MCP server name is extracted from mcp__<server>__<tool> names."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [
            {"type": "tool_use", "name": "mcp__playwright__browser_navigate", "input": {"url": "http://localhost"}},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.mcp_servers == ["playwright"]
    # MCP tool also goes into tools list
    assert "mcp__playwright__browser_navigate" in rec.tools


def test_slash_command_extraction_from_list_content():
    """Slash commands are extracted from text blocks in list-form content."""
    line = json.dumps({
        "type": "user", "sessionId": "s",
        "message": {"role": "user", "content": [
            {"type": "text", "text": "<command-name>/clear</command-name>"},
        ]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.slash_commands == ["/clear"]


def test_slash_command_extraction_from_string_content():
    """Slash commands are extracted from plain string content."""
    line = json.dumps({
        "type": "user", "sessionId": "s",
        "message": {"role": "user", "content": "<command-name>/compact</command-name>"},
    })
    rec = parse_lines([line]).records[0]
    assert rec.slash_commands == ["/compact"]


def test_multiple_slash_commands_in_one_message():
    """Multiple slash commands in a single message are all captured."""
    line = json.dumps({
        "type": "user", "sessionId": "s",
        "message": {
            "role": "user",
            "content": "<command-name>/clear</command-name> then <command-name>/compact</command-name>",
        },
    })
    rec = parse_lines([line]).records[0]
    assert "/clear" in rec.slash_commands
    assert "/compact" in rec.slash_commands


def test_empty_new_lists_by_default():
    """Records without relevant content have empty new list fields."""
    line = json.dumps({
        "type": "assistant", "sessionId": "s",
        "message": {"model": "claude-opus-4-8", "content": [{"type": "text"}]},
    })
    rec = parse_lines([line]).records[0]
    assert rec.languages == []
    assert rec.frameworks == []
    assert rec.skills == []
    assert rec.subagents == []
    assert rec.mcp_servers == []
    assert rec.slash_commands == []


def test_tech_fixture_end_to_end():
    """tech.jsonl exercises all signal types in the parser."""
    p = parse_session_file(FIX / "tech.jsonl")
    assert p.session_id == "sess-tech"
    assert p.ai_title == "Tech signals test"

    all_languages = [lang for r in p.records for lang in r.languages]
    all_frameworks = [fw for r in p.records for fw in r.frameworks]
    all_skills = [sk for r in p.records for sk in r.skills]
    all_subagents = [sa for r in p.records for sa in r.subagents]
    all_mcp = [mcp for r in p.records for mcp in r.mcp_servers]
    all_slash = [sc for r in p.records for sc in r.slash_commands]

    assert "Python" in all_languages           # Write /src/main.py
    assert "TypeScript/React" in all_languages  # Edit /src/App.tsx
    assert "JSON" in all_languages              # Write /app/package.json
    assert "Python" in all_frameworks           # Bash: uv run pytest
    assert "pytest" in all_frameworks           # Bash: uv run pytest
    assert "Node.js" in all_frameworks          # Write /app/package.json
    assert "superpowers:writing-plans" in all_skills
    assert "Explore" in all_subagents
    assert "playwright" in all_mcp
    assert "/clear" in all_slash
