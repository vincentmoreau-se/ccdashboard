# Live updates use periodic polling of store.all_summaries() — a deliberate simplification; no filesystem watcher needed at this scale.
from __future__ import annotations

from datetime import datetime, timezone

from app.models import SessionSummary
from app.store import SessionStore


def active_sessions(store: SessionStore) -> list[SessionSummary]:
    return [s for s in store.all_summaries() if s.is_active]


def live_snapshot(store: SessionStore) -> dict:
    active = active_sessions(store)
    return {
        "active": [s.model_dump(mode="json") for s in active],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
