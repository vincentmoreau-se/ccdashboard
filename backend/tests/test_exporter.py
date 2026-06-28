from datetime import datetime, timezone

import httpx
import pytest

from app.config import Settings
from app.exporter import Exporter, build_payload
from app.models import ProjectSummary, SessionSummary, Usage


def _summary(sid, enriched_title="secret") -> SessionSummary:
    ts = datetime(2026, 6, 12, tzinfo=timezone.utc)
    return SessionSummary(
        session_id=sid, project="p", file_path=f"/x/{sid}.jsonl",
        ai_title=enriched_title, git_branch="main", cc_version="2.1",
        started_at=ts, ended_at=ts, models=["claude-opus-4-8"], provider="anthropic",
        message_count=2, usage=Usage(input=10, output=5), cost=1.0, cost_known=True,
    )


def test_payload_strips_enriched_by_default():
    s = _summary("a")
    p = ProjectSummary(name="p", path="/x")
    settings = Settings(export_include_enriched=False)
    payload = build_payload([s], [p], settings, sent_at="2026-06-28T00:00:00Z")
    assert payload["schema_version"] == 1
    sess = payload["sessions"][0]
    assert sess["ai_title"] is None
    assert sess["git_branch"] is None
    assert sess["usage"]["input"] == 10  # aggregates kept


def test_payload_keeps_enriched_when_enabled():
    settings = Settings(export_include_enriched=True)
    payload = build_payload([_summary("a")], [], settings, sent_at="t")
    assert payload["sessions"][0]["ai_title"] == "secret"


@pytest.mark.asyncio
async def test_send_once_advances_cursor_on_success():
    settings = Settings(export_enabled=True, export_endpoint="http://mock/ingest",
                        export_token="tok")
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
