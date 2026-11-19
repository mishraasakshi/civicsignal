"""Refuse to start in production with unsafe settings.

In development (ENVIRONMENT=development) problems are only printed as warnings.
Anywhere else (staging, production, ...) the app stops at startup with a clear list,
so a weak secret or an open CORS policy can never reach the internet by accident.
"""

import logging
from urllib.parse import urlparse

log = logging.getLogger(__name__)

# Secrets that are written in this repository (docs, docker-compose) - never valid in production
KNOWN_PUBLIC_SECRETS = {
    "change-me-to-a-secure-random-secret-key-in-production",
    "civicsignal-local-secret-key-2026",
}
KNOWN_PUBLIC_DB_PASSWORDS = {"civicpassword", "readonlypassword", "postgres", "password"}
LOCAL_HOSTS = {"localhost", "127.0.0.1"}


def find_problems(settings) -> list[str]:
    problems: list[str] = []

    secret = settings.JWT_SECRET_KEY
    if secret in KNOWN_PUBLIC_SECRETS:
        problems.append(
            "JWT_SECRET_KEY is a value published in this repository - generate a new random one"
        )
    elif len(secret) < 32:
        problems.append("JWT_SECRET_KEY is shorter than 32 characters")

    for name in ("DATABASE_URL", "DATABASE_READONLY_URL"):
        password = urlparse(getattr(settings, name)).password
        if password in KNOWN_PUBLIC_DB_PASSWORDS:
            problems.append(f"{name} uses a default password - set a strong, unique one")

    for origin in settings.CORS_ORIGINS:
        parsed = urlparse(origin)
        if origin.strip() == "*":
            problems.append("CORS_ORIGINS contains '*' - list the exact frontend address instead")
        elif parsed.scheme != "https" and parsed.hostname not in LOCAL_HOSTS:
            problems.append(f"CORS origin {origin!r} is not https")

    return problems


def enforce(settings) -> None:
    problems = find_problems(settings)
    if not problems:
        return
    if settings.ENVIRONMENT == "development":
        for p in problems:
            log.warning("[production check] %s (allowed in development only)", p)
        return
    raise RuntimeError(
        "Refusing to start: unsafe settings for ENVIRONMENT="
        + settings.ENVIRONMENT
        + "\n - "
        + "\n - ".join(problems)
    )
