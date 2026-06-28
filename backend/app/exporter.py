from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.metrics import list_projects
from app.models import ProjectSummary, SessionSummary

ENRICHED_FIELDS = ("ai_title", "git_branch", "cc_version")


def _session_payload(s: SessionSummary, include_enriched: bool) -> dict:
    data = s.model_dump(mode="json")
    if not include_enriched:
        for field in ENRICHED_FIELDS:
            data[field] = None
    return data


def build_payload(
    summaries: list[SessionSummary],
    projects: list[ProjectSummary],
    settings: Settings,
    sent_at: str,
) -> dict:
    return {
        "schema_version": 1,
        "source": {
            "machine_id": settings.export_machine_id,
            "user_id": settings.export_user_id,
            "instance_id": settings.export_instance_id,
        },
        "sent_at": sent_at,
        "sessions": [
            _session_payload(s, settings.export_include_enriched) for s in summaries
        ],
        "projects": [p.model_dump(mode="json") for p in projects],
    }


class Exporter:
    def __init__(self, settings: Settings, store):
        self._settings = settings
        self._store = store
        self._cursor: dict[str, str] = {}

    def _key(self, s: SessionSummary) -> str:
        return (s.ended_at or s.started_at).isoformat() if (s.ended_at or s.started_at) else ""

    def pending(self, summaries: list[SessionSummary]) -> list[SessionSummary]:
        out = []
        for s in summaries:
            if self._cursor.get(s.session_id) != self._key(s):
                out.append(s)
        return out

    async def send_once(self, client: httpx.AsyncClient) -> bool:
        summaries = self._store.all_summaries()
        pending = self.pending(summaries)
        if not pending:
            return True
        payload = build_payload(
            pending,
            list_projects(summaries),
            self._settings,
            sent_at=datetime.now(timezone.utc).isoformat(),
        )
        headers = {"Authorization": f"Bearer {self._settings.export_token}"}
        try:
            resp = await client.post(
                self._settings.export_endpoint, json=payload, headers=headers, timeout=30
            )
        except httpx.HTTPError:
            return False
        if resp.status_code // 100 != 2:
            return False
        for s in pending:
            self._cursor[s.session_id] = self._key(s)
        return True

    async def run_periodic(self) -> None:
        if not self._settings.export_enabled or not self._settings.export_endpoint:
            return
        async with httpx.AsyncClient() as client:
            while True:
                await self.send_once(client)
                await asyncio.sleep(self._settings.export_interval_minutes * 60)
