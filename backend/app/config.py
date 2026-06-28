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

    export_enabled: bool = False
    export_endpoint: str | None = None
    export_token: str | None = None
    export_interval_minutes: int = 15
    export_include_enriched: bool = False
    export_machine_id: str = socket.gethostname()
    export_user_id: str = "unknown"
    export_instance_id: str = "default"


@lru_cache
def get_settings() -> Settings:
    return Settings()
