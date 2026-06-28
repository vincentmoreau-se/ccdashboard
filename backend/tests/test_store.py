import shutil
from pathlib import Path

from app.config import Settings
from app.store import SessionStore

FIX = Path(__file__).parent / "fixtures"


def _make_settings(tmp_path) -> Settings:
    projects = tmp_path / "projects" / "-home-vemore-workspace-countscore"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "sample.jsonl", projects / "sess-1.jsonl")
    return Settings(
        projects_dir=tmp_path / "projects",
        pricing_path=Path(__file__).resolve().parents[2] / "pricing.json",
    )


def test_all_summaries(tmp_path):
    store = SessionStore(_make_settings(tmp_path))
    summaries = store.all_summaries()
    assert len(summaries) == 1
    assert summaries[0].session_id == "sess-1"
    assert summaries[0].project == "-home-vemore-workspace-countscore"


def test_cache_reuses_until_mtime_changes(tmp_path, monkeypatch):
    settings = _make_settings(tmp_path)
    store = SessionStore(settings)
    f = next((settings.projects_dir).rglob("*.jsonl"))

    calls = {"n": 0}
    import app.store as store_mod
    real = store_mod.parse_session_file

    def counting_parse(path):
        calls["n"] += 1
        return real(path)

    monkeypatch.setattr(store_mod, "parse_session_file", counting_parse)
    store.get_summary(f)
    store.get_summary(f)
    assert calls["n"] == 1  # second call served from cache
