import hashlib
import json

from app.config import Settings
from app.identity import resolve_user_id


def _settings(tmp_path, **kw):
    return Settings(
        claude_settings_path=tmp_path / "settings.json",
        export_anon_id_path=tmp_path / ".ccdashboard_user_id",
        **kw,
    )


def test_key_present_hashes_anthropic_api_key(tmp_path):
    (tmp_path / "settings.json").write_text(
        json.dumps({"env": {"ANTHROPIC_API_KEY": "sk-test-123"}})
    )
    expected = hashlib.sha256(b"sk-test-123").hexdigest()
    assert resolve_user_id(_settings(tmp_path)) == f"key:{expected}"


def test_missing_settings_file_falls_back_to_anon(tmp_path):
    uid = resolve_user_id(_settings(tmp_path))
    assert uid.startswith("anon:")
    assert (tmp_path / ".ccdashboard_user_id").exists()


def test_anon_id_is_stable_across_calls(tmp_path):
    s = _settings(tmp_path)
    first = resolve_user_id(s)
    second = resolve_user_id(s)
    assert first == second
    assert first.startswith("anon:")


def test_malformed_or_keyless_settings_fall_back_to_anon(tmp_path):
    # malformed JSON
    (tmp_path / "settings.json").write_text("{not json")
    assert resolve_user_id(_settings(tmp_path)).startswith("anon:")
    # valid JSON but no env / empty key
    (tmp_path / "settings.json").write_text(json.dumps({"env": {"ANTHROPIC_API_KEY": "  "}}))
    assert resolve_user_id(_settings(tmp_path)).startswith("anon:")
    (tmp_path / "settings.json").write_text(json.dumps({"permissions": {}}))
    assert resolve_user_id(_settings(tmp_path)).startswith("anon:")


def test_explicit_override_wins_and_touches_nothing(tmp_path):
    (tmp_path / "settings.json").write_text(
        json.dumps({"env": {"ANTHROPIC_API_KEY": "sk-test-123"}})
    )
    s = _settings(tmp_path, export_user_id="manual-xyz")
    assert resolve_user_id(s) == "manual-xyz"
    assert not (tmp_path / ".ccdashboard_user_id").exists()
