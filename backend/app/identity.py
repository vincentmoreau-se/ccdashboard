"""Resolve the export `source.user_id`.

Precedence: explicit `export_user_id` override > SHA-256 of the hackathon API key
found in `~/.claude/settings.json` (`env.ANTHROPIC_API_KEY`) > a stable random
UUID persisted locally. The raw key never leaves the machine — only its hash is
sent, so a central server can map `sha256(key) -> team` precomputed out-of-band.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _read_api_key(settings_path: Path) -> str | None:
    try:
        data = json.loads(settings_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    env = data.get("env")
    key = env.get("ANTHROPIC_API_KEY") if isinstance(env, dict) else None
    return key.strip() if isinstance(key, str) and key.strip() else None


def _read_or_create_anon_id(path: Path) -> str:
    try:
        existing = path.read_text().strip()
        if existing:
            return existing
    except OSError:
        pass
    new_id = str(uuid.uuid4())
    try:
        path.write_text(new_id)
    except OSError:
        pass  # non-persistent fallback if home is read-only
    return new_id


def resolve_user_id(settings) -> str:
    # 1. explicit manual override wins, used verbatim
    if settings.export_user_id:
        return settings.export_user_id
    # 2. hackathon key in settings.json -> team-mappable id
    key = _read_api_key(settings.claude_settings_path)
    if key:
        return f"key:{_sha256(key)}"
    # 3. stable anonymous fallback
    return f"anon:{_read_or_create_anon_id(settings.export_anon_id_path)}"
