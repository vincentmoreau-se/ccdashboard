import shutil
import time
from pathlib import Path

from app.config import Settings
from app.store import SessionStore
from app.watcher import active_sessions, live_snapshot

FIX = Path(__file__).parent / "fixtures"


def _store(tmp_path) -> SessionStore:
    projects = tmp_path / "projects" / "-home-vemore-workspace-countscore"
    projects.mkdir(parents=True)
    dest = projects / "sess-1.jsonl"
    shutil.copy(FIX / "sample.jsonl", dest)
    now = time.time()
    import os
    os.utime(dest, (now, now))  # fresh mtime -> active
    settings = Settings(
        projects_dir=tmp_path / "projects",
        pricing_path=Path(__file__).resolve().parents[2] / "pricing.json",
        live_active_threshold_seconds=3600,
    )
    return SessionStore(settings)


def test_active_sessions(tmp_path):
    store = _store(tmp_path)
    active = active_sessions(store)
    assert len(active) == 1
    assert active[0].is_active is True


def test_live_snapshot_shape(tmp_path):
    snap = live_snapshot(_store(tmp_path))
    assert "active" in snap
    assert "generated_at" in snap
    assert len(snap["active"]) == 1
