from __future__ import annotations
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.exceptions import AreebFetchError, to_http_exception
from app.models.schemas import HealthResponse
from app.services.job_manager import job_manager
from app.services.converter import converter_service
from app.api import analyze, downloads, websocket, history, settings as settings_api, playlist, batch, images, pdf, scanner

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("areebfetch")
_START = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await job_manager.start()
    yield
    await job_manager.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.state.limiter = analyze.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins() + (["*"] if settings.DEBUG else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AreebFetchError)
async def areeb_handler(request: Request, exc: AreebFetchError):
    http_exc = to_http_exception(exc)
    return JSONResponse(status_code=http_exc.status_code, content=http_exc.detail)


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"error": "internal_error", "message": "Unexpected error"})


app.include_router(analyze.router, prefix="/api")
app.include_router(downloads.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")
app.include_router(playlist.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")
app.include_router(scanner.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    yt_ver = None
    try:
        import yt_dlp
        yt_ver = yt_dlp.version.__version__
    except Exception:
        pass

    disk_mb = 0.0
    try:
        total = sum(f.stat().st_size for f in settings.DOWNLOAD_DIR.rglob("*") if f.is_file())
        disk_mb = total / (1024 * 1024)
    except Exception:
        pass

    active = sum(
        1 for j in await job_manager.list_jobs(100)
        if j.status in ("downloading", "processing", "merging", "waiting")
    )

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(time.time() - _START, 1),
        active_jobs=active,
        disk_usage_mb=round(disk_mb, 1),
        yt_dlp_version=yt_ver,
        ffmpeg_available=converter_service.available,
    )


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "phases": "1-16 complete",
    }