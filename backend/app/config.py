import secrets
from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageBackend(StrEnum):
    DATABASE = "database"
    """Measurements in InfluxDB, trials in a SQL database."""
    MEMORY = "memory"
    """Everything in memory, lost on restart. For tests and quick demos."""


class Settings(BaseSettings):
    """Application settings, read from environment variables prefixed with POLYGRAPHE_."""

    model_config = SettingsConfigDict(env_prefix="POLYGRAPHE_", env_file=".env", extra="ignore")

    device_token: SecretStr = SecretStr("change-me")

    # Needed to create, edit, start and stop trials. Watching needs nothing.
    operator_password: SecretStr = SecretStr("dummy")
    operator_session_hours: float = 12
    # Signs operator sessions. Random by default: sessions then end when the server restarts.
    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))

    storage_backend: StorageBackend = StorageBackend.DATABASE
    influx_url: str = "http://localhost:8086"
    influx_token: SecretStr = SecretStr("polygraphe-dev-token")
    influx_org: str = "polygraphe"
    influx_raw_bucket: str = "raw"
    influx_processed_bucket: str = "processed"

    database_url: str = "sqlite+aiosqlite:///./polygraphe.db"

    # Public path prefix when served behind a reverse proxy that strips it (e.g. "/api"),
    # so the interactive docs at /docs point to the right URLs.
    root_path: str = ""

    dummy_enabled: bool = True
    dummy_device_id: str = "dummy-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
