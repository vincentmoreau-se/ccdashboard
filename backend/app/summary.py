from __future__ import annotations

from pathlib import Path

from app.models import SessionSummary, Usage
from app.parser import ParsedSession
from app.pricing import PriceTable, detect_provider


def is_priceable_model(model: str | None) -> bool:
    """True only for real, billable model ids.

    Claude Code writes some assistant turns with placeholder pseudo-models wrapped
    in angle brackets (e.g. ``<synthetic>`` for local-command output and compaction
    notices). These carry zero token usage and have no price entry, so they must be
    skipped: otherwise the missing price would flip ``cost_known`` to False for the
    whole session even though no real cost is unaccounted for.
    """
    return bool(model) and not model.startswith("<")


def summarize_session(
    parsed: ParsedSession,
    *,
    file_path: Path,
    project: str,
    table: PriceTable,
    default_provider: str,
    active_threshold_seconds: int,
    now_ts: float,
    mtime: float,
) -> SessionSummary:
    total = Usage()
    tool_counts: dict[str, int] = {}
    content_kind_counts: dict[str, int] = {}
    models: list[str] = []
    timestamps = []
    lines_generated = 0
    cost = 0.0
    cache_savings = 0.0
    cost_known = True
    provider = default_provider
    provider_resolved = False
    git_branch = None
    cc_version = None
    cwd = None

    for r in parsed.records:
        if r.timestamp:
            timestamps.append(r.timestamp)
        git_branch = git_branch or r.git_branch
        cc_version = cc_version or r.cc_version
        cwd = cwd or r.cwd
        for t in r.tools:
            tool_counts[t] = tool_counts.get(t, 0) + 1
        for k in r.content_kinds:
            content_kind_counts[k] = content_kind_counts.get(k, 0) + 1
        lines_generated += r.lines_generated
        if r.type == "assistant" and is_priceable_model(r.model):
            if not provider_resolved:
                provider = detect_provider(r.model, default_provider)
                provider_resolved = True
            if r.model not in models:
                models.append(r.model)
            total = total.add(r.usage)
            c, known = table.cost_for_usage(r.usage, r.model, provider)
            cost += c
            cache_savings += table.cache_savings_for_usage(r.usage, r.model, provider)
            cost_known = cost_known and known

    started = min(timestamps) if timestamps else None
    ended = max(timestamps) if timestamps else None
    duration = (ended - started).total_seconds() if started and ended else None

    return SessionSummary(
        session_id=parsed.session_id or file_path.stem,
        project=project,
        cwd=cwd,
        file_path=str(file_path),
        ai_title=parsed.ai_title,
        started_at=started,
        ended_at=ended,
        duration_seconds=duration,
        is_active=(now_ts - mtime) <= active_threshold_seconds,
        models=models,
        provider=provider,
        git_branch=git_branch,
        cc_version=cc_version,
        message_count=len(parsed.records),
        usage=total,
        lines_generated=lines_generated,
        cost=cost,
        cost_known=cost_known,
        cache_savings=cache_savings,
        tool_counts=tool_counts,
        content_kind_counts=content_kind_counts,
        skipped_lines=parsed.skipped_lines,
    )
