import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app, get_store
from app.store import SessionStore

FIX = Path(__file__).parent / "fixtures"


def _client(tmp_path):
    projects = tmp_path / "projects" / "-home-vemore-workspace-countscore"
    projects.mkdir(parents=True)
    shutil.copy(FIX / "sample.jsonl", projects / "sess-1.jsonl")
    settings = Settings(
        projects_dir=tmp_path / "projects",
        pricing_path=Path(__file__).resolve().parents[2] / "pricing.json",
    )
    app.dependency_overrides[get_store] = lambda: SessionStore(settings)
    return TestClient(app)


def test_overview(tmp_path):
    client = _client(tmp_path)
    r = client.get("/api/overview")
    assert r.status_code == 200
    assert r.json()["session_count"] == 1


def test_session_detail(tmp_path):
    client = _client(tmp_path)
    r = client.get("/api/sessions/sess-1")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["session_id"] == "sess-1"
    assert len(body["messages"]) == 3


def test_session_404(tmp_path):
    client = _client(tmp_path)
    assert client.get("/api/sessions/nope").status_code == 404
