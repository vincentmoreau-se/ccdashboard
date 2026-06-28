from pathlib import Path

from app.config import Settings


def test_defaults():
    s = Settings()
    assert s.projects_dir.name == "projects"
    assert s.export_enabled is False
    assert s.currency == "€"
    assert s.export_user_id is None  # derived at export time, not a literal


def test_env_override(monkeypatch):
    monkeypatch.setenv("CCDASH_PROJECTS_DIR", "/tmp/x")
    monkeypatch.setenv("CCDASH_EXPORT_ENABLED", "true")
    monkeypatch.setenv("CCDASH_EXPORT_USER_ID", "manual-xyz")
    s = Settings()
    assert s.projects_dir == Path("/tmp/x")
    assert s.export_enabled is True
    assert s.export_user_id == "manual-xyz"  # explicit override kept verbatim
