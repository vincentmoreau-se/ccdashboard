import hashlib
import json
from datetime import datetime, timezone

import httpx
import pytest

from app.config import Settings
from app.exporter import Exporter, build_payload
from app.models import ProjectSummary, SessionSummary, Usage


def _settings(tmp_path, **kw) -> Settings:
    """Settings with identity paths isolated to tmp_path (no real ~/.claude writes)."""
    return Settings(
        claude_settings_path=tmp_path / "settings.json",
        export_anon_id_path=tmp_path / ".ccdashboard_user_id",
        **kw,
    )


def _summary(sid, enriched_title="secret") -> SessionSummary:
    ts = datetime(2026, 6, 12, tzinfo=timezone.utc)
    return SessionSummary(
        session_id=sid, project="p", file_path=f"/x/{sid}.jsonl",
        cwd="/home/me/work/p",
        ai_title=enriched_title, git_branch="main", cc_version="2.1",
        started_at=ts, ended_at=ts, models=["claude-opus-4-8"], provider="anthropic",
        message_count=2, usage=Usage(input=10, output=5), cost=1.0, cost_known=True,
    )


def test_payload_strips_enriched_by_default(tmp_path):
    s = _summary("a")
    p = ProjectSummary(name="p", path="/x")
    settings = _settings(tmp_path, export_include_enriched=False)
    payload = build_payload([s], [p], settings, sent_at="2026-06-28T00:00:00Z")
    assert payload["schema_version"] == 1
    sess = payload["sessions"][0]
    assert sess["ai_title"] is None
    assert sess["git_branch"] is None
    assert sess["cc_version"] is None
    # cwd / file_path are absolute local paths — must NOT leak by default (spec §7).
    assert sess["cwd"] is None
    assert sess["file_path"] is None
    assert sess["usage"]["input"] == 10  # aggregates kept


def test_payload_keeps_enriched_when_enabled(tmp_path):
    settings = _settings(tmp_path, export_include_enriched=True)
    payload = build_payload([_summary("a")], [], settings, sent_at="t")
    sess = payload["sessions"][0]
    assert sess["ai_title"] == "secret"
    # opt-in: file paths are present only when include_enriched is True.
    assert sess["cwd"] == "/home/me/work/p"
    assert sess["file_path"] == "/x/a.jsonl"


def test_payload_user_id_falls_back_to_anon(tmp_path):
    payload = build_payload([_summary("a")], [], _settings(tmp_path), sent_at="t")
    assert payload["source"]["user_id"].startswith("anon:")


def test_payload_user_id_hashes_hackathon_key(tmp_path):
    (tmp_path / "settings.json").write_text(
        json.dumps({"env": {"ANTHROPIC_API_KEY": "sk-test-123"}})
    )
    expected = hashlib.sha256(b"sk-test-123").hexdigest()
    payload = build_payload([_summary("a")], [], _settings(tmp_path), sent_at="t")
    assert payload["source"]["user_id"] == f"key:{expected}"


def test_payload_includes_new_aggregate_maps(tmp_path):
    """All 8 new maps introduced in SessionSummary must appear in the export payload.

    The exporter serialises via model_dump(mode='json') with no field whitelist,
    so this test locks the contract: a regression (e.g. accidental whitelist) would
    be caught immediately.
    """
    ts = datetime(2026, 6, 28, tzinfo=timezone.utc)
    s = SessionSummary(
        session_id="b",
        project="p",
        file_path="/x/b.jsonl",
        started_at=ts,
        language_counts={"Python": 12, "TypeScript": 5},
        framework_counts={"React": 3},
        builtin_tool_counts={"Bash": 40, "Edit": 12},
        user_tool_counts={"Skill": 3, "playwright": 2},
        skill_counts={"frontend-design": 1},
        mcp_server_counts={"github": 7},
        subagent_counts={"general-purpose": 4},
        slash_command_counts={"/review": 2},
    )
    settings = _settings(tmp_path)
    payload = build_payload([s], [], settings, sent_at="2026-06-28T00:00:00Z")
    sess = payload["sessions"][0]

    assert sess["language_counts"] == {"Python": 12, "TypeScript": 5}
    assert sess["framework_counts"] == {"React": 3}
    assert sess["builtin_tool_counts"] == {"Bash": 40, "Edit": 12}
    assert sess["user_tool_counts"] == {"Skill": 3, "playwright": 2}
    assert sess["skill_counts"] == {"frontend-design": 1}
    assert sess["mcp_server_counts"] == {"github": 7}
    assert sess["subagent_counts"] == {"general-purpose": 4}
    assert sess["slash_command_counts"] == {"/review": 2}


@pytest.mark.asyncio
async def test_send_once_advances_cursor_on_success(tmp_path):
    settings = _settings(tmp_path, export_enabled=True,
                         export_endpoint="http://mock/ingest", export_token="tok")
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = request.content
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)

    class FakeStore:
        def all_summaries(self_inner):
            return [_summary("a")]

    exporter = Exporter(settings, FakeStore())
    async with httpx.AsyncClient(transport=transport) as client:
        ok = await exporter.send_once(client)
    assert ok is True
    assert captured["auth"] == "Bearer tok"
    # second send: nothing pending -> still True, no new data
    async with httpx.AsyncClient(transport=transport) as client:
        assert exporter.pending(FakeStore().all_summaries()) == []
