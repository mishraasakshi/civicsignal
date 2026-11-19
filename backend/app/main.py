from __future__ import annotations

from app.core.config import settings
from app.core.production_checks import enforce
from app.core.security_headers import SecurityHeadersMiddleware
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

enforce(settings)  # stop here if production settings are unsafe

# Interactive API docs only in development (or when ENABLE_DOCS=true)
SHOW_DOCS = (
    settings.ENABLE_DOCS
    if settings.ENABLE_DOCS is not None
    else settings.ENVIRONMENT == "development"
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CivicSignal: AI Complaint-Intelligence Platform for Amity University Lucknow",
    version=settings.VERSION,
    docs_url="/docs" if SHOW_DOCS else None,
    redoc_url="/redoc" if SHOW_DOCS else None,
    openapi_url="/openapi.json" if SHOW_DOCS else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # needed for the session cookie
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],  # only what the API uses
    allow_headers=["Content-Type", "Authorization"],
)
app.add_middleware(SecurityHeadersMiddleware, https_only=settings.ENVIRONMENT != "development")


# Standardized Error Format: {"error": {"code": str, "message": str}}
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}},
        headers=getattr(exc, "headers", None),  # keep Retry-After, WWW-Authenticate, ...
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Name the field and the problem, but never echo what was sent (it could be a password)
    parts = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path"))
        parts.append(
            f"{field}: {err.get('msg', 'invalid')}" if field else err.get("msg", "invalid")
        )
    return JSONResponse(
        status_code=422,  # Unprocessable Content (the named constant changed between versions)
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed: " + "; ".join(parts),
            }
        },
    )


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


if not settings.FRONTEND_DIST:  # when the website is served, "/" is the website instead

    @app.get("/", tags=["Root"])
    def root():
        return {
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "operational",
            "docs": "/docs",
            "pilot_target": "Amity University Lucknow",
        }


# ---------------------------------------------------------------------------
# Routers (Phase 5)
# ---------------------------------------------------------------------------
from app.api.classify import router as classify_router  # noqa: E402

app.include_router(classify_router, prefix=settings.API_V1_STR)
from app.api.similar import router as similar_router  # noqa: E402

app.include_router(similar_router, prefix=settings.API_V1_STR)
from app.api.complaints import router as complaints_router  # noqa: E402

app.include_router(complaints_router, prefix=settings.API_V1_STR)
from app.api.auth import router as auth_router  # noqa: E402

app.include_router(auth_router, prefix=settings.API_V1_STR)
from app.api.insights import router as insights_router  # noqa: E402

app.include_router(insights_router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Website (production): serve the built React app from the same address as the API,
# so the login cookie is first-party and no CORS is needed.
# ---------------------------------------------------------------------------
if settings.FRONTEND_DIST:
    from app.core.frontend import mount_frontend  # noqa: E402

    mount_frontend(app, settings.FRONTEND_DIST)
