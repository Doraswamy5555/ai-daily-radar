"""Password hashing and signed-cookie helpers for local user accounts."""

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.app.settings import get_settings


SESSION_COOKIE_NAME = "ai_daily_radar_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
settings = get_settings()
_serializer = URLSafeTimedSerializer(settings.session_secret, salt="ai-daily-radar-session")


def hash_password(password: str) -> str:
    """Create a bcrypt password hash; the original password is never stored."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Safely compare a password to its stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_session_value(user_id: int) -> str:
    """Sign a user ID for storage in an HTTP-only cookie."""
    return _serializer.dumps({"user_id": user_id})


def read_session_user_id(value: str | None) -> int | None:
    """Read a valid, unexpired signed session cookie."""
    if not value:
        return None
    try:
        data = _serializer.loads(value, max_age=SESSION_MAX_AGE_SECONDS)
        return int(data["user_id"])
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return None
