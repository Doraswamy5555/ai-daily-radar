"""Environment-based settings shared by local and production deployments."""

import os
import secrets
from dataclasses import dataclass


DEFAULT_SQLITE_URL = "sqlite:///database/ai_daily_radar.db"


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    session_secret: str
    session_cookie_secure: bool


def get_settings() -> Settings:
    """Read deployment settings while keeping SQLite as the development default."""
    app_env = os.getenv("APP_ENV", "development").lower()
    database_url = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
    configured_secret = os.getenv("SESSION_SECRET")

    if app_env == "production" and not configured_secret:
        raise RuntimeError("SESSION_SECRET must be set when APP_ENV=production")

    return Settings(
        app_env=app_env,
        database_url=database_url,
        session_secret=configured_secret or secrets.token_urlsafe(32),
        session_cookie_secure=app_env == "production",
    )
