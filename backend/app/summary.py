from __future__ import annotations

from pathlib import Path

from app.models import CostBreakdown, SessionSummary, Usage
from app.parser import ParsedSession
from app.pricing import PriceTable, detect_provider
from app.taxonomy import classify_tool


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
    cost_breakdown = CostBreakdown()
    cache_savings = 0.0
    cost_known = True
    provider = default_provider
    provider_resolved = False
    git_branch = None
    cc_version = None
    cwd = None
    language_counts: dict[str, int] = {}
    framework_counts: dict[str, int] = {}
    builtin_tool_counts: dict[str, int] = {}
    user_tool_counts: dict[str, int] = {}
    skill_counts: dict[str, int] = {}
    mcp_server_counts: dict[str, int] = {}
    subagent_counts: dict[str, int] = {}
    slash_command_counts: dict[str, int] = {}
    seen_message_ids: set[str] = set()

    for r in parsed.records:
        if r.timestamp:
            timestamps.append(r.timestamp)
        git_branch = git_branch or r.git_branch
        cc_version = cc_version or r.cc_version
        cwd = cwd or r.cwd
        for t in r.tools:
            tool_counts[t] = tool_counts.get(t, 0) + 1
            cat = classify_tool(t)
            if cat == "builtin":
                builtin_tool_counts[t] = builtin_tool_counts.get(t, 0) + 1
            else:
                user_tool_counts[t] = user_tool_counts.get(t, 0) + 1
        for k in r.content_kinds:
            content_kind_counts[k] = content_kind_counts.get(k, 0) + 1
        lines_generated += r.lines_generated
        for lang in r.languages:
            language_counts[lang] = language_counts.get(lang, 0) + 1
        for fw in r.frameworks:
            framework_counts[fw] = framework_counts.get(fw, 0) + 1
        for skill in r.skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        for sa in r.subagents:
            subagent_counts[sa] = subagent_counts.get(sa, 0) + 1
        for mcp in r.mcp_servers:
            mcp_server_counts[mcp] = mcp_server_counts.get(mcp, 0) + 1
        for sc in r.slash_commands:
            slash_command_counts[sc] = slash_command_counts.get(sc, 0) + 1
        if r.type == "assistant" and is_priceable_model(r.model):
            if not provider_resolved:
                provider = detect_provider(r.model, default_provider)
                provider_resolved = True
            if r.model not in models:
                models.append(r.model)
            # Claude Code écrit une même réponse d'assistant sur plusieurs lignes
            # (une par bloc de contenu), toutes avec le même message.id et le même
            # objet usage. On ne compte donc usage/coût qu'une fois par message.id
            # (repli sur uuid, unique par ligne, si l'id manque). Les agrégats
            # par-bloc (outils, lignes, kinds) ci-dessus restent comptés par ligne.
            dedup_key = r.message_id or r.uuid
            if dedup_key is None or dedup_key not in seen_message_ids:
                if dedup_key is not None:
                    seen_message_ids.add(dedup_key)
                total = total.add(r.usage)
                bd = table.cost_breakdown_for_usage(r.usage, r.model, provider)
                if bd is None:
                    cost_known = False
                else:
                    cost_breakdown = cost_breakdown.add(bd)
                    cost += bd.total()
                cache_savings += table.cache_savings_for_usage(
                    r.usage, r.model, provider
                )

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
        cost_breakdown=cost_breakdown,
        cache_savings=cache_savings,
        tool_counts=tool_counts,
        content_kind_counts=content_kind_counts,
        skipped_lines=parsed.skipped_lines,
        language_counts=language_counts,
        framework_counts=framework_counts,
        builtin_tool_counts=builtin_tool_counts,
        user_tool_counts=user_tool_counts,
        skill_counts=skill_counts,
        mcp_server_counts=mcp_server_counts,
        subagent_counts=subagent_counts,
        slash_command_counts=slash_command_counts,
    )
