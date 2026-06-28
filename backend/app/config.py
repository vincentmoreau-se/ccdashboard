import socket
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CCDASH_", env_file=".env")

    projects_dir: Path = Path.home() / ".claude" / "projects"
    currency: str = "€"
    pricing_path: Path = Path(__file__).resolve().parents[2] / "pricing.json"
    default_provider: str = "anthropic"
    live_active_threshold_seconds: int = 30
    # Allow any localhost origin so the SPA works on a random dev port. A browser
    # cannot forge a localhost Origin from an external site, so this stays safe.
    cors_origin_regex: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    export_enabled: bool = False
    export_endpoint: str | None = None
    export_token: str | None = None
    export_interval_minutes: int = 15
    # When > 0, overrides export_interval_minutes. Use a small value (e.g. 30s)
    # for near-real-time live tracking on the central server (whose live window
    # is ~120s — push more often than that to keep sessions "live").
    export_interval_seconds: int = 0
    export_include_enriched: bool = False
    export_machine_id: str = socket.gethostname()
    export_user_id: str | None = None
    export_instance_id: str = "default"
    claude_settings_path: Path = Path.home() / ".claude" / "settings.json"
    claude_skills_dir: Path = Path.home() / ".claude" / "skills"
    claude_plugins_path: Path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    claude_global_config_path: Path = Path.home() / ".claude.json"
    claude_agents_dir: Path = Path.home() / ".claude" / "agents"
    claude_commands_dir: Path = Path.home() / ".claude" / "commands"
    export_anon_id_path: Path = Path.home() / ".claude" / ".ccdashboard_user_id"


@lru_cache
def get_settings() -> Settings:
    return Settings()
