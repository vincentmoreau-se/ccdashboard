from __future__ import annotations

import time
from pathlib import Path

from app.config import Settings
from app.models import CostBreakdown, MessageRecord, SessionSummary
from app.parser import parse_session_file
from app.pricing import PriceTable
from app.summary import is_priceable_model, summarize_session


class SessionStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._table = PriceTable.load(settings.pricing_path)
        self._cache: dict[str, tuple[float, SessionSummary]] = {}

    def reload_pricing(self) -> None:
        self._table = PriceTable.load(self._settings.pricing_path)
        self._cache.clear()

    def project_name_for(self, file_path: Path) -> str:
        return file_path.parent.name

    def get_summary(self, file_path: Path) -> SessionSummary:
        mtime = file_path.stat().st_mtime
        key = str(file_path)
        cached = self._cache.get(key)
        if cached and cached[0] == mtime:
            return cached[1]
        parsed = parse_session_file(file_path)
        summary = summarize_session(
            parsed,
            file_path=file_path,
            project=self.project_name_for(file_path),
            table=self._table,
            default_provider=self._settings.default_provider,
            active_threshold_seconds=self._settings.live_active_threshold_seconds,
            now_ts=time.time(),
            mtime=mtime,
        )
        self._cache[key] = (mtime, summary)
        return summary

    def with_message_costs(
        self, records: list[MessageRecord], provider: str
    ) -> list[MessageRecord]:
        """Attach a per-message cost to each record for the session timeline.

        Non-priceable turns (user messages, ``<synthetic>`` placeholders) have no
        billable model, so they are reported as a known cost of ``0.0`` rather than
        flagged unknown.

        A single assistant response is written across several lines sharing one
        ``message.id`` (and an identical ``usage``). The cost is attached only to the
        first line of each ``message.id`` (``0.0`` on the others) so the timeline sum
        matches the deduplicated session cost in :func:`summarize_session`.
        """
        out: list[MessageRecord] = []
        seen_message_ids: set[str] = set()
        for r in records:
            breakdown = CostBreakdown()
            if not is_priceable_model(r.model):
                cost, known = 0.0, True
            else:
                dedup_key = r.message_id or r.uuid
                if dedup_key is not None and dedup_key in seen_message_ids:
                    cost, known = 0.0, True
                else:
                    if dedup_key is not None:
                        seen_message_ids.add(dedup_key)
                    bd = self._table.cost_breakdown_for_usage(
                        r.usage, r.model, provider
                    )
                    if bd is None:
                        cost, known = 0.0, False
                    else:
                        breakdown = bd
                        cost, known = bd.total(), True
            out.append(
                r.model_copy(
                    update={
                        "cost": cost,
                        "cost_known": known,
                        "cost_breakdown": breakdown,
                    }
                )
            )
        return out

    def all_summaries(self) -> list[SessionSummary]:
        root = self._settings.projects_dir
        if not root.exists():
            return []
        summaries: list[SessionSummary] = []
        for path in sorted(root.glob("*/*.jsonl")):
            try:
                summaries.append(self.get_summary(path))
            except OSError:
                continue
        return summaries
