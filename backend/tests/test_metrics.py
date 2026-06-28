from datetime import datetime, timezone

import pytest

from app.models import SessionSummary, Usage
from app.metrics import build_overview, list_projects, project_detail


def _s(session_id, project, model, inp, out, day) -> SessionSummary:
    ts = datetime(2026, 6, day, 12, 0, tzinfo=timezone.utc)
    return SessionSummary(
        session_id=session_id, project=project, file_path=f"/x/{session_id}.jsonl",
        started_at=ts, ended_at=ts, models=[model], provider="anthropic",
        message_count=2, usage=Usage(input=inp, output=out), cost=1.0, cost_known=True,
    )


def test_build_overview():
    summaries = [
        _s("a", "proj1", "claude-opus-4-8", 100, 10, 11),
        _s("b", "proj1", "claude-opus-4-8", 200, 20, 12),
        _s("c", "proj2", "claude-haiku-4-5", 50, 5, 12),
    ]
    ov = build_overview(summaries)
    assert ov.session_count == 3
    assert ov.total_usage.input == 350
    assert ov.total_cost == 3.0
    models = {m.model: m for m in ov.by_model}
    assert models["claude-opus-4-8"].usage.input == 300
    assert models["claude-opus-4-8"].session_count == 2
    projects = {p.name: p for p in ov.by_project}
    assert projects["proj1"].session_count == 2
    days = {b.date: b for b in ov.timeseries}
    assert days["2026-06-12"].session_count == 2


def test_project_detail():
    summaries = [_s("a", "proj1", "claude-opus-4-8", 100, 10, 11)]
    agg, sessions = project_detail(summaries, "proj1")
    assert agg.session_count == 1
    assert len(sessions) == 1


def test_project_detail_unknown():
    with pytest.raises(KeyError):
        project_detail([], "nonexistent")


def test_sort_survives_missing_timestamps():
    no_ts = SessionSummary(
        session_id="z", project="proj_nots", file_path="/x/z.jsonl",
        models=["claude-opus-4-8"], provider="anthropic",
        message_count=2, usage=Usage(input=1, output=1), cost=1.0, cost_known=True,
    )
    summaries = [_s("a", "proj1", "claude-opus-4-8", 100, 10, 11), no_ts]

    # list_projects must not raise when a project has no timestamps.
    projects = list_projects(summaries)
    assert {p.name for p in projects} == {"proj1", "proj_nots"}

    # project_detail must not raise sorting sessions without timestamps.
    mixed = [no_ts, _s("b", "proj_nots", "claude-opus-4-8", 5, 1, 12)]
    agg, sessions = project_detail(mixed, "proj_nots")
    assert agg.session_count == 2
    assert len(sessions) == 2
