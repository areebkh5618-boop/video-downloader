"""
API routes – Phase 6 hardened version.
"""
from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.exceptions import (
    AreebFetchError, http_exception_from_areeb,
    MediaAnalysisError, DownloadError, JobNotFoundError
)
from app.models.schemas import (
    AnalyzeRequest, AnalyzeResponse, DownloadRequest,
    JobInfo, JobStatus, HealthResponse, ProgressUpdate
)
from app.services.job_manager import job_manager
from app.services.media_service import media_service

logger = logging.getLogger("areebfetch.api")
router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# App start time for uptime
_START_TIME = time.time()


# ─── Health ───────────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health():
    import shutil
    import subprocess

    # yt-dlp version
    yt_ver = None
    try:
        import yt_dlp
        yt_ver = yt_dlp.version.__version__
    except Exception:
        pass

    # ffmpeg
    ffmpeg_ok = shutil.which("ffmpeg") is not None

    # disk usage of download dir
    disk_mb = 0.0
    try:
        total = sum(f.stat().st_size for f in settings.DOWNLOAD_DIR.rglob("*") if f.is_file())
        disk_mb = total / (1024 * 1024)
    except Exception:
        pass

    active = sum(1 for j in (await job_manager.list_jobs(200)) if j.status in (
        JobStatus.DOWNLOADING, JobStatus.PROCESSING, JobStatus.PENDING
    ))

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(time.time() - _START_TIME, 1),
        active_jobs=active,
        disk_usage_mb=round(disk_mb, 1),
        yt_dlp_version=yt_ver,
        ffmpeg_available=ffmpeg_ok,
    )


# ─── Analyze ──────────────────────────────────────────────────────────────
@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit(settings.RATE_LIMIT)
async def analyze(request: Request, body: AnalyzeRequest):
    try:
        info = await media_service.analyze(str(body.url))
        return AnalyzeResponse(data=info)
    except AreebFetchError as e:
        raise http_exception_from_areeb(e)
    except Exception as e:
        logger.exception("Analyze unexpected error")
        raise HTTPException(500, detail={"error": "internal_error", "message": str(e)[:150]})


# ─── Download (async job) ─────────────────────────────────────────────────
@router.post("/download", response_model=JobInfo)
@limiter.limit("10/minute")
async def start_download(request: Request, body: DownloadRequest, background_tasks: BackgroundTasks):
    if not await job_manager.can_start_download():
        raise HTTPException(429, detail={
            "error": "too_many_downloads",
            "message": f"Maximum concurrent downloads ({settings.MAX_CONCURRENT_DOWNLOADS}) reached."
        })

    job = await job_manager.create_job(str(body.url))
    job.title = None  # will be filled later

    async def _run():
        try:
            # Quick re-analyze to get title if needed
            try:
                info = await media_service.analyze(str(body.url))
                job.title = info.title
            except Exception:
                pass

            await media_service.download(
                job=job,
                format_id=body.format_id,
                audio_only=body.audio_only,
                audio_format=body.audio_format,
                video_quality=body.video_quality,
            )
        except Exception as e:
            logger.error(f"Background download failed: {e}")
            if job.status not in (JobStatus.FAILED, JobStatus.COMPLETED):
                job.update(status=JobStatus.FAILED, error=str(e)[:300])

    background_tasks.add_task(_run)
    return job.to_info()


# ─── Job status ───────────────────────────────────────────────────────────
@router.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise http_exception_from_areeb(JobNotFoundError(job_id))
    return job.to_info()


@router.get("/jobs", response_model=list[JobInfo])
async def list_jobs(limit: int = 30):
    return await job_manager.list_jobs(limit=min(limit, 100))


# ─── File download (secure) ───────────────────────────────────────────────
@router.get("/download/file/{job_id}")
async def download_file(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise http_exception_from_areeb(JobNotFoundError(job_id))
    if job.status != JobStatus.COMPLETED or not job.download_path:
        raise HTTPException(400, detail={"error": "not_ready", "message": "File not ready yet"})
    if not job.download_path.exists():
        raise HTTPException(404, detail={"error": "file_missing", "message": "File has been cleaned up"})

    return FileResponse(
        path=job.download_path,
        filename=job.filename or job.download_path.name,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{job.filename}"'},
    )


# ─── WebSocket progress ───────────────────────────────────────────────────
@router.websocket("/ws/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    job = await job_manager.get_job(job_id)
    if not job:
        await websocket.send_json({"error": "job_not_found"})
        await websocket.close()
        return

    queue: asyncio.Queue = asyncio.Queue()

    def on_update(update: ProgressUpdate):
        try:
            queue.put_nowait(update.model_dump(mode="json"))
        except Exception:
            pass

    job.subscribe(on_update)

    # Send current state immediately
    await websocket.send_json(job.to_info().model_dump(mode="json"))

    try:
        while True:
            # Also allow client pings
            try:
                data = await asyncio.wait_for(queue.get(), timeout=25.0)
                await websocket.send_json(data)
                if data.get("status") in ("completed", "failed", "cancelled"):
                    break
            except asyncio.TimeoutError:
                # keepalive
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        job.unsubscribe(on_update)


# ─── SSE fallback ─────────────────────────────────────────────────────────
@router.get("/sse/{job_id}")
async def sse_progress(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise http_exception_from_areeb(JobNotFoundError(job_id))

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        def on_update(update: ProgressUpdate):
            try:
                queue.put_nowait(update)
            except Exception:
                pass

        job.subscribe(on_update)
        # initial
        yield f"data: {job.to_info().model_dump_json()}\n\n"

        try:
            while True:
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield f"data: {update.model_dump_json()}\n\n"
                    if update.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                        break
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            job.unsubscribe(on_update)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )