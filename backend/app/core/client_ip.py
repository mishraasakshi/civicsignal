"""Who is calling? The visitor's real IP address, also when the app runs behind a proxy.

Hosting platforms put a proxy in front of the app. The app then sees the PROXY's address,
so every visitor would share one rate limit. Each trusted proxy appends the address it
received the request from to the X-Forwarded-For header, so the real visitor is found by
counting TRUSTED_PROXY_HOPS entries from the RIGHT. Entries further left were written by
the visitor's own browser and can be faked, so they are ignored.

TRUSTED_PROXY_HOPS = 0 (default, local development): use the direct connection's address.
TRUSTED_PROXY_HOPS = 1: one proxy in front (e.g. Azure Container Apps).
"""

from app.core.config import settings
from fastapi import Request


def client_ip(request: Request, hops: int | None = None) -> str:
    hops = settings.TRUSTED_PROXY_HOPS if hops is None else hops
    if hops > 0:
        forwarded = [
            p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()
        ]
        if len(forwarded) >= hops:
            return forwarded[-hops]
    return request.client.host if request.client else "unknown"
