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
    assert sess["usage"]["input"] == 10  # aggregates kept


def test_payload_keeps_enriched_when_enabled(tmp_path):
    settings = _settings(tmp_path, export_include_enriched=True)
    payload = build_payload([_summary("a")], [], settings, sent_at="t")
    assert payload["sessions"][0]["ai_title"] == "secret"


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
