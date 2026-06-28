"""Tests for tooling_config module and /api/tooling-config endpoint."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.tooling_config import InstalledTooling, discover_installed_tooling


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_home(tmp_path: Path) -> Settings:
    """Build a fake ~/.claude tree and return a Settings pointing at it."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)

    # Skills: one skill directory
    skills_dir = claude_dir / "skills"
    skill_dir = skills_dir / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# My Skill")

    # installed_plugins.json
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "installed_plugins.json").write_text(
        json.dumps({"plugins": {"superpowers@official": {}}})
    )

    # settings.json
    settings_json = {
        "enabledPlugins": {"superpowers@official": True, "x@y": False},
        "hooks": {
            "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}],
            "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "echo bye"}]}],
        },
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings_json))

    # ~/.claude.json with mcpServers
    global_config = {
        "mcpServers": {"foo": {"command": "foo-cmd"}},
        "projects": {
            "/p": {"mcpServers": {"bar": {"command": "bar-cmd"}}},
        },
    }
    (tmp_path / ".claude.json").write_text(json.dumps(global_config))

    # agents/ dir
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "my-agent.md").write_text("# My Agent")

    # commands/ dir
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "my-command.md").write_text("# My Command")

    return Settings(
        claude_skills_dir=skills_dir,
        claude_plugins_path=plugins_dir / "installed_plugins.json",
        claude_settings_path=claude_dir / "settings.json",
        claude_global_config_path=tmp_path / ".claude.json",
        claude_agents_dir=agents_dir,
        claude_commands_dir=commands_dir,
    )


# ---------------------------------------------------------------------------
# Unit tests: discover_installed_tooling
# ---------------------------------------------------------------------------

def test_skills(tmp_path):
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    assert "my-skill" in result.skills


def test_plugins_installed(tmp_path):
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    assert result.plugins_installed == ["superpowers@official"]


def test_plugins_enabled(tmp_path):
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    assert result.plugins_enabled == ["superpowers@official"]
    assert "x@y" not in result.plugins_enabled


def test_mcp_servers(tmp_path):
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    assert set(result.mcp_servers) == {"foo", "bar"}


def test_hooks_count(tmp_path):
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    # 2 hook-type keys each with 1 matcher list of length 1 → total = 2
    assert result.hooks == 2


def test_subagents(tmp_path):
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    assert "my-agent" in result.subagents


def test_commands(tmp_path):
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    assert "my-command" in result.commands


def test_full_result(tmp_path):
    """Smoke test: all fields populated as expected."""
    settings = _make_fake_home(tmp_path)
    result = discover_installed_tooling(settings)
    assert isinstance(result, InstalledTooling)
    assert len(result.skills) >= 1
    assert len(result.plugins_installed) >= 1
    assert len(result.plugins_enabled) >= 1
    assert len(result.mcp_servers) >= 2
    assert result.hooks > 0
    assert len(result.subagents) >= 1
    assert len(result.commands) >= 1


# ---------------------------------------------------------------------------
# Resilience tests: missing / invalid files → empty, no exception
# ---------------------------------------------------------------------------

def test_resilience_missing_paths(tmp_path):
    """All paths point to non-existent locations → empty InstalledTooling, no raise."""
    settings = Settings(
        claude_skills_dir=tmp_path / "no-skills",
        claude_plugins_path=tmp_path / "no-plugins.json",
        claude_settings_path=tmp_path / "no-settings.json",
        claude_global_config_path=tmp_path / "no-claude.json",
        claude_agents_dir=tmp_path / "no-agents",
        claude_commands_dir=tmp_path / "no-commands",
    )
    result = discover_installed_tooling(settings)
    assert result == InstalledTooling()
    assert result.hooks == 0
    assert result.skills == []
    assert result.mcp_servers == []


def test_resilience_invalid_json(tmp_path):
    """Invalid JSON files → empty results, no exception."""
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json !!!")
    settings = Settings(
        claude_skills_dir=tmp_path / "no-skills",
        claude_plugins_path=bad,
        claude_settings_path=bad,
        claude_global_config_path=bad,
        claude_agents_dir=tmp_path / "no-agents",
        claude_commands_dir=tmp_path / "no-commands",
    )
    result = discover_installed_tooling(settings)
    assert result.plugins_installed == []
    assert result.plugins_enabled == []
    assert result.mcp_servers == []
    assert result.hooks == 0


def test_plugins_installed_fallback_to_root_keys(tmp_path):
    """If installed_plugins.json lacks a 'plugins' key, fall back to root keys."""
    plugins_file = tmp_path / "installed_plugins.json"
    plugins_file.write_text(json.dumps({"some-plugin@x": {}, "other@y": {}}))
    settings = Settings(
        claude_plugins_path=plugins_file,
        claude_skills_dir=tmp_path / "no-skills",
        claude_settings_path=tmp_path / "no-settings.json",
        claude_global_config_path=tmp_path / "no-claude.json",
        claude_agents_dir=tmp_path / "no-agents",
        claude_commands_dir=tmp_path / "no-commands",
    )
    result = discover_installed_tooling(settings)
    assert set(result.plugins_installed) == {"some-plugin@x", "other@y"}


def test_plugins_installed_present_but_not_dict(tmp_path):
    """If 'plugins' key is present but not a dict, return [] (no root fallback)."""
    plugins_file = tmp_path / "installed_plugins.json"
    plugins_file.write_text(json.dumps({"plugins": [1, 2, 3]}))
    settings = Settings(
        claude_plugins_path=plugins_file,
        claude_skills_dir=tmp_path / "no-skills",
        claude_settings_path=tmp_path / "no-settings.json",
        claude_global_config_path=tmp_path / "no-claude.json",
        claude_agents_dir=tmp_path / "no-agents",
        claude_commands_dir=tmp_path / "no-commands",
    )
    result = discover_installed_tooling(settings)
    assert result.plugins_installed == []


def test_plugins_enabled_as_list(tmp_path):
    """If enabledPlugins is already a list, return it as-is."""
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"enabledPlugins": ["a@x", "b@y"]}))
    settings = Settings(
        claude_settings_path=settings_file,
        claude_skills_dir=tmp_path / "no-skills",
        claude_plugins_path=tmp_path / "no-plugins.json",
        claude_global_config_path=tmp_path / "no-claude.json",
        claude_agents_dir=tmp_path / "no-agents",
        claude_commands_dir=tmp_path / "no-commands",
    )
    result = discover_installed_tooling(settings)
    assert set(result.plugins_enabled) == {"a@x", "b@y"}


# ---------------------------------------------------------------------------
# API tests: GET /api/tooling-config
# ---------------------------------------------------------------------------

def test_api_tooling_config_200(tmp_path):
    """Endpoint returns 200 and correct shape."""
    settings = _make_fake_home(tmp_path)
    # Override both get_settings (used directly by tooling_config route) and
    # get_store (used by other routes — ensures override fixture clears properly)
    app.dependency_overrides[get_settings] = lambda: settings

    client = TestClient(app)
    r = client.get("/api/tooling-config")
    assert r.status_code == 200
    body = r.json()
    assert "skills" in body
    assert "plugins_installed" in body
    assert "plugins_enabled" in body
    assert "mcp_servers" in body
    assert "hooks" in body
    assert "subagents" in body
    assert "commands" in body
    # Spot-check values
    assert "my-skill" in body["skills"]
    assert "superpowers@official" in body["plugins_installed"]
    assert set(body["mcp_servers"]) == {"foo", "bar"}


def test_api_tooling_config_resilient_empty(tmp_path):
    """Endpoint returns 200 with empty lists when all paths are missing."""
    settings = Settings(
        claude_skills_dir=tmp_path / "no-skills",
        claude_plugins_path=tmp_path / "no-plugins.json",
        claude_settings_path=tmp_path / "no-settings.json",
        claude_global_config_path=tmp_path / "no-claude.json",
        claude_agents_dir=tmp_path / "no-agents",
        claude_commands_dir=tmp_path / "no-commands",
    )
    app.dependency_overrides[get_settings] = lambda: settings

    client = TestClient(app)
    r = client.get("/api/tooling-config")
    assert r.status_code == 200
    body = r.json()
    assert body["skills"] == []
    assert body["hooks"] == 0
