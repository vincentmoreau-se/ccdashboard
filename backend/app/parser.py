from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

from app.models import MessageRecord, Usage


class ParsedSession(BaseModel):
    session_id: str | None = None
    ai_title: str | None = None
    records: list[MessageRecord] = Field(default_factory=list)
    skipped_lines: int = 0


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _usage_from(message: dict) -> Usage:
    u = message.get("usage") or {}
    cc = u.get("cache_creation") or {}
    st = u.get("server_tool_use") or {}
    return Usage(
        input=u.get("input_tokens", 0) or 0,
        output=u.get("output_tokens", 0) or 0,
        cache_read=u.get("cache_read_input_tokens", 0) or 0,
        cache_write_5m=cc.get("ephemeral_5m_input_tokens", 0) or 0,
        cache_write_1h=cc.get("ephemeral_1h_input_tokens", 0) or 0,
        web_search=st.get("web_search_requests", 0) or 0,
        web_fetch=st.get("web_fetch_requests", 0) or 0,
    )


def _count_lines(text) -> int:
    if not isinstance(text, str) or not text:
        return 0
    return len(text.splitlines())


def _lines_generated_from(name: str, inp) -> int:
    """Lines produced by a write-class tool, from its ``input`` (never ``old_string``)."""
    if not isinstance(inp, dict):
        return 0
    if name == "Write":
        return _count_lines(inp.get("content"))
    if name == "Edit":
        return _count_lines(inp.get("new_string"))
    if name == "MultiEdit":
        edits = inp.get("edits")
        if not isinstance(edits, list):
            return 0
        return sum(
            _count_lines(e.get("new_string")) for e in edits if isinstance(e, dict)
        )
    if name == "NotebookEdit":
        return _count_lines(inp.get("new_source"))
    return 0


def _record_from(obj: dict) -> MessageRecord:
    message = obj.get("message") or {}
    content = message.get("content")
    tools: list[str] = []
    kinds: list[str] = []
    lines_generated = 0
    if isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            kind = c.get("type")
            if kind:
                kinds.append(kind)
            if kind == "tool_use" and c.get("name"):
                tools.append(c["name"])
                lines_generated += _lines_generated_from(c["name"], c.get("input"))
    return MessageRecord(
        uuid=obj.get("uuid"),
        parent_uuid=obj.get("parentUuid"),
        timestamp=_parse_ts(obj.get("timestamp")),
        type=obj.get("type", "unknown"),
        model=message.get("model"),
        git_branch=obj.get("gitBranch"),
        cwd=obj.get("cwd"),
        cc_version=obj.get("version"),
        usage=_usage_from(message),
        tools=tools,
        content_kinds=list(dict.fromkeys(kinds)),
        lines_generated=lines_generated,
    )


def parse_lines(lines: Iterable[str]) -> ParsedSession:
    parsed = ParsedSession()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            parsed.skipped_lines += 1
            continue
        if not isinstance(obj, dict):
            parsed.skipped_lines += 1
            continue
        if parsed.session_id is None and obj.get("sessionId"):
            parsed.session_id = obj["sessionId"]
        if obj.get("type") == "ai-title":
            parsed.ai_title = obj.get("aiTitle")
            continue
        if obj.get("type") in {"user", "assistant", "system"}:
            parsed.records.append(_record_from(obj))
    return parsed


def parse_session_file(path: Path) -> ParsedSession:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return parse_lines(fh)
