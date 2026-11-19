"""Passwords (bcrypt) and login tokens (JWT)."""

import logging
from datetime import UTC, datetime, timedelta

import bcrypt
from app.core.config import settings
from jose import JWTError, jwt

log = logging.getLogger(__name__)
DEFAULT_SECRET = "change-me-to-a-secure-random-secret-key-in-production"

if settings.JWT_SECRET_KEY == DEFAULT_SECRET or len(settings.JWT_SECRET_KEY) < 32:
    if settings.ENVIRONMENT != "development":
        raise RuntimeError(
            "JWT_SECRET_KEY is the default or too short - set a long random value in .env"
        )
    log.warning("JWT_SECRET_KEY is the default/too short - fine for local tests only")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:  # malformed hash or password longer than 72 bytes
        return False


# Used when the email does not exist, so a wrong email takes as long as a wrong password
# (otherwise response time would reveal which emails are registered).
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user_id: int, role: str, lifetime: timedelta | None = None) -> str:
    lifetime = lifetime or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires = datetime.now(UTC) + lifetime
    payload = {"sub": str(user_id), "role": role, "exp": expires}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Return the user id inside a valid, unexpired token, else None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
