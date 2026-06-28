from __future__ import annotations

import time
from pathlib import Path

from app.config import Settings
from app.models import SessionSummary
from app.parser import parse_session_file
from app.pricing import PriceTable
from app.summary import summarize_session


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
