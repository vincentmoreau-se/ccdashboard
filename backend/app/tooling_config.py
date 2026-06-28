"""Discover installed Claude Code tooling from ~/.claude config files.

This module is I/O + config-parsing only; it has no dependency on session
aggregation logic.

MCP servers are discovered best-effort from ~/.claude.json (.mcpServers keys
+ .projects[*].mcpServers keys). This *under-estimates* installed MCP servers:
servers provided by plugins are not listed in these files and are therefore
invisible here.

hooks count: if the `hooks` key in settings.json is a dict, we count the total
number of entries across all hook-type lists (sum of list lengths). If it is a
list we count its length directly. If absent or not countable we return 0. This
reflects "total configured hook matchers".
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel

from app.config import Settings

logger = logging.getLogger(__name__)


class InstalledTooling(BaseModel):
    skills: list[str] = []
    plugins_installed: list[str] = []
    plugins_enabled: list[str] = []
    mcp_servers: list[str] = []
    hooks: int = 0
    subagents: list[str] = []
    commands: list[str] = []


def discover_installed_tooling(settings: Settings) -> InstalledTooling:
    """Read each config source independently; any unexpected error returns empty."""
    try:
        return _discover(settings)
    except Exception:
        logger.exception("Unexpected error in discover_installed_tooling; returning empty")
        return InstalledTooling()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _discover(settings: Settings) -> InstalledTooling:
    skills = _read_skills(settings.claude_skills_dir)
    plugins_installed = _read_plugins_installed(settings.claude_plugins_path)
    plugins_enabled = _read_plugins_enabled(settings.claude_settings_path)
    mcp_servers = _read_mcp_servers(settings.claude_global_config_path)
    hooks = _read_hooks(settings.claude_settings_path)
    subagents = _read_md_stems(settings.claude_agents_dir)
    commands = _read_md_stems(settings.claude_commands_dir)

    return InstalledTooling(
        skills=skills,
        plugins_installed=plugins_installed,
        plugins_enabled=plugins_enabled,
        mcp_servers=mcp_servers,
        hooks=hooks,
        subagents=subagents,
        commands=commands,
    )


def _read_skills(skills_dir: Path) -> list[str]:
    try:
        if not skills_dir.is_dir():
            return []
        return sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
    except Exception:
        logger.exception("Failed to read skills dir %s", skills_dir)
        return []


def _read_plugins_installed(plugins_path: Path) -> list[str]:
    """Keys of .plugins in installed_plugins.json; tolerates structural variation."""
    try:
        if not plugins_path.is_file():
            return []
        data = json.loads(plugins_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            if "plugins" in data:
                # Key present: use its dict keys, else [] (don't fall through).
                plugins = data["plugins"]
                return list(plugins.keys()) if isinstance(plugins, dict) else []
            # Key absent: fall back to top-level keys as names.
            return list(data.keys())
        return []
    except Exception:
        logger.exception("Failed to read plugins installed file %s", plugins_path)
        return []


def _read_plugins_enabled(settings_path: Path) -> list[str]:
    """Names with truthy value from enabledPlugins in settings.json."""
    try:
        if not settings_path.is_file():
            return []
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        enabled = data.get("enabledPlugins")
        if enabled is None:
            return []
        if isinstance(enabled, dict):
            return sorted(name for name, val in enabled.items() if val)
        if isinstance(enabled, list):
            return sorted(enabled)
        return []
    except Exception:
        logger.exception("Failed to read enabled plugins from %s", settings_path)
        return []


def _read_mcp_servers(global_config_path: Path) -> list[str]:
    """Best-effort union of .mcpServers keys and .projects[*].mcpServers keys."""
    try:
        if not global_config_path.is_file():
            return []
        data = json.loads(global_config_path.read_text(encoding="utf-8"))
        names: set[str] = set()
        if isinstance(data.get("mcpServers"), dict):
            names.update(data["mcpServers"].keys())
        projects = data.get("projects")
        if isinstance(projects, dict):
            for proj in projects.values():
                if isinstance(proj, dict) and isinstance(proj.get("mcpServers"), dict):
                    names.update(proj["mcpServers"].keys())
        return sorted(names)
    except Exception:
        logger.exception("Failed to read MCP servers from %s", global_config_path)
        return []


def _read_hooks(settings_path: Path) -> int:
    """Total number of configured hook matchers from settings.json .hooks."""
    try:
        if not settings_path.is_file():
            return 0
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks = data.get("hooks")
        if hooks is None:
            return 0
        if isinstance(hooks, dict):
            # Sum lengths of matcher lists across all hook-type keys
            total = 0
            for v in hooks.values():
                if isinstance(v, list):
                    total += len(v)
                else:
                    total += 1
            return total
        if isinstance(hooks, list):
            return len(hooks)
        return 0
    except Exception:
        logger.exception("Failed to read hooks from %s", settings_path)
        return 0


def _read_md_stems(directory: Path) -> list[str]:
    """Stems of *.md files in directory."""
    try:
        if not directory.is_dir():
            return []
        return sorted(p.stem for p in directory.iterdir() if p.suffix == ".md")
    except Exception:
        logger.exception("Failed to read md stems from %s", directory)
        return []
