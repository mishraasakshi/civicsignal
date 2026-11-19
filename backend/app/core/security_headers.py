"""Security headers added to every response.

- nosniff:          browsers must not guess file types
- frame-ancestors:  no other site may show us inside a frame (clickjacking)
- referrer:         don't leak full URLs to other sites
- permissions:      this API never needs camera, microphone or location
- CSP:              API responses are JSON and may load nothing at all
                    (/docs needs the Swagger files from a CDN, so it gets a looser policy)
- HSTS:             outside development, always use HTTPS for a year
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

API_CSP = "default-src 'none'; frame-ancestors 'none'"
# The website (when the backend serves it): only our own files + Google Fonts, no inline scripts
PAGE_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
    "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)
API_PATHS = ("/api", "/health", "/openapi.json")
DOCS_CSP = (
    "default-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; frame-ancestors 'none'"
)
DOCS_PATHS = ("/docs", "/redoc")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, https_only: bool):
        super().__init__(app)
        self.https_only = https_only

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        h = response.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        path = request.url.path
        if path.startswith(DOCS_PATHS):
            csp = DOCS_CSP
        elif path.startswith(API_PATHS):
            csp = API_CSP
        else:
            csp = PAGE_CSP  # the website and its files
        h.setdefault("Content-Security-Policy", csp)
        if self.https_only:
            h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
