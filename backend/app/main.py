from __future__ import annotations
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CivicSignal: AI Complaint-Intelligence Platform for Amity University Lucknow",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"Input validation failed: {exc.errors()}",
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
