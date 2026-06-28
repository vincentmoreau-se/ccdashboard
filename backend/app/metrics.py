from __future__ import annotations

from datetime import datetime, timezone

from app.models import (
    ModelStat,
    Overview,
    ProjectSummary,
    SessionSummary,
    TimeBucket,
    Usage,
)


def _merge_models(existing: list[str], new: list[str]) -> list[str]:
    out = list(existing)
    for m in new:
        if m not in out:
            out.append(m)
    return out


def _merge_counts(acc: dict[str, int], new: dict[str, int]) -> None:
    for k, v in new.items():
        acc[k] = acc.get(k, 0) + v


def list_projects(summaries: list[SessionSummary]) -> list[ProjectSummary]:
    acc: dict[str, ProjectSummary] = {}
    for s in summaries:
        p = acc.get(s.project)
        if p is None:
            p = ProjectSummary(name=s.project, path=s.cwd or s.project)
            acc[s.project] = p
        p.session_count += 1
        p.usage = p.usage.add(s.usage)
        p.lines_generated += s.lines_generated
        p.cost += s.cost
        p.cost_known = p.cost_known and s.cost_known
        p.models = _merge_models(p.models, s.models)
        last = s.ended_at or s.started_at
        if last and (p.last_activity is None or last > p.last_activity):
            p.last_activity = last
    return sorted(
        acc.values(),
        key=lambda x: (
            x.last_activity is not None,
            x.last_activity or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )


def build_overview(summaries: list[SessionSummary]) -> Overview:
    total = Usage()
    total_cost = 0.0
    cache_savings = 0.0
    cost_known = True
    model_acc: dict[str, ModelStat] = {}
    day_acc: dict[str, TimeBucket] = {}
    tool_acc: dict[str, int] = {}
    content_kind_acc: dict[str, int] = {}

    for s in summaries:
        total = total.add(s.usage)
        total_cost += s.cost
        cache_savings += s.cache_savings
        cost_known = cost_known and s.cost_known
        _merge_counts(tool_acc, s.tool_counts)
        _merge_counts(content_kind_acc, s.content_kind_counts)

        model_key = s.models[0] if s.models else "(none)"
        ms = model_acc.get(model_key)
        if ms is None:
            ms = ModelStat(model=model_key, provider=s.provider)
            model_acc[model_key] = ms
        ms.usage = ms.usage.add(s.usage)
        ms.cost += s.cost
        ms.cost_known = ms.cost_known and s.cost_known
        ms.session_count += 1

        day = (s.started_at or s.ended_at)
        if day:
            key = day.date().isoformat()
            tb = day_acc.get(key)
            if tb is None:
                tb = TimeBucket(date=key)
                day_acc[key] = tb
            tb.session_count += 1
            tb.usage = tb.usage.add(s.usage)
            tb.cost += s.cost

    top_sessions = sorted(summaries, key=lambda s: s.cost, reverse=True)[:10]

    return Overview(
        session_count=len(summaries),
        total_usage=total,
        total_cost=total_cost,
        cost_known=cost_known,
        cache_savings=cache_savings,
        by_model=sorted(model_acc.values(), key=lambda m: m.cost, reverse=True),
        by_project=list_projects(summaries),
        timeseries=sorted(day_acc.values(), key=lambda b: b.date),
        tool_counts=tool_acc,
        content_kind_counts=content_kind_acc,
        top_sessions=top_sessions,
    )


def project_detail(
    summaries: list[SessionSummary], project: str
) -> tuple[ProjectSummary, list[SessionSummary]]:
    sessions = [s for s in summaries if s.project == project]
    if not sessions:
        raise KeyError(project)
    agg = list_projects(sessions)[0]
    sessions = sorted(
        sessions,
        key=lambda s: (
            (s.ended_at or s.started_at) is not None,
            (s.ended_at or s.started_at)
            or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )
    return agg, sessions
