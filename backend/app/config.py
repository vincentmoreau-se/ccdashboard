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
    export_include_enriched: bool = False
    export_machine_id: str = socket.gethostname()
    export_user_id: str | None = None
    export_instance_id: str = "default"
    claude_settings_path: Path = Path.home() / ".claude" / "settings.json"
    export_anon_id_path: Path = Path.home() / ".claude" / ".ccdashboard_user_id"


@lru_cache
def get_settings() -> Settings:
    return Settings()
