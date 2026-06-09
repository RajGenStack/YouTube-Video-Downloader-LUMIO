"""
main.py
FastAPI application factory.
Registers middleware, exception handlers, routers, and lifecycle events.
"""
import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.cleanup import cleanup_loop
from app.config import get_settings
from app.logger import logger
from app.routes import limiter, router

settings = get_settings()


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")

    # Ensure temp directory exists
    Path(settings.TMP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"Temp directory ready: {settings.TMP_DIR}")

    # Verify FFmpeg is available
    import shutil
    if shutil.which("ffmpeg"):
        logger.info("FFmpeg found ✓")
    else:
        logger.warning("FFmpeg NOT found — audio conversion and video merging will fail!")

    # Verify yt-dlp
    import yt_dlp
    logger.info(f"yt-dlp version: {yt_dlp.version.__version__} ✓")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_loop())
    logger.info("Background cleanup task started ✓")

    yield  # ← app runs here

    # ── SHUTDOWN ─────────────────────────────────────────────────────────
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info(f"{settings.APP_NAME} shut down cleanly.")


# ── Request timing middleware ────────────────────────────────────────────────
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        if request.url.path not in ("/health",):
            logger.info(
                f"{request.method} {request.url.path} "
                f"→ {response.status_code} [{elapsed_ms}ms]"
            )
        return response


# ── Security headers middleware ───────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]          = "DENY"
        response.headers["X-XSS-Protection"]         = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


# ── App factory ──────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-grade YouTube downloader API.\n\n"
            "Supports MP3 (70k–620k) and MP4 (144p–8K HDR) downloads.\n\n"
            "All processing happens server-side via yt-dlp + FFmpeg."
        ),
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # ── Rate limiter ──────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
        expose_headers=["Content-Disposition", "X-Lumio-Quality", "X-Lumio-Mode"],
        max_age=600,
    )

    # ── GZip compression ──────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Custom middlewares ────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TimingMiddleware)

    # ── Exception handlers ────────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        messages = []
        for e in errors:
            field = " → ".join(str(loc) for loc in e["loc"] if loc != "body")
            messages.append(f"{field}: {e['msg']}" if field else e["msg"])
        detail = "; ".join(messages)
        logger.warning(f"Validation error on {request.url.path}: {detail}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": detail, "code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={"detail": f"Route '{request.url.path}' not found.", "code": "NOT_FOUND"},
        )

    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc):
        return JSONResponse(
            status_code=405,
            content={"detail": "Method not allowed.", "code": "METHOD_NOT_ALLOWED"},
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        logger.exception(f"Unhandled 500 on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred.", "code": "INTERNAL_ERROR"},
        )

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(router)

    # ── Root redirect ─────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        return {"service": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}

    return app


# ── Entry point ──────────────────────────────────────────────────────────────
app = create_app()
