from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from pathlib import Path
import re

from app.core.config import settings
from app.core.security import validate_url
from app.core.exceptions import AreebFetchError, to_http_exception, JobNotFoundError
from app.models.schemas import DownloadRequest, JobInfo, JobStatus
from app.services.job_manager import job_manager
from app.services.downloader import downloader_service
from app.services.extractor import extractor_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/download", response_model=JobInfo)
@limiter.limit("15/minute")
async def start_download(request: Request, body: DownloadRequest, background_tasks: BackgroundTasks):
    try:
        url = validate_url(body.url)
    except AreebFetchError as e:
        raise to_http_exception(e)

    if not await job_manager.can_start():
        raise HTTPException(429, detail={
            "error": "too_many_downloads",
            "message": f"Max concurrent downloads ({settings.MAX_CONCURRENT_DOWNLOADS}) reached.",
        })

    job = await job_manager.create_job(
        url,
        type=body.type,
        quality=body.quality,
        format=body.format,
        bitrate=body.bitrate,
        format_id=body.format_id,
        save_thumbnail=body.save_thumbnail,
    )

    async def _run():
        try:
            try:
                info = await extractor_service.analyze(url)
                job.title = info.title
                job.thumbnail = info.thumbnail
            except Exception:
                pass
            await downloader_service.download(job)
        except Exception as e:
            if job.status not in (JobStatus.FAILED, JobStatus.COMPLETED, JobStatus.CANCELLED):
                job.update(status=JobStatus.FAILED, error=str(e)[:300])

    background_tasks.add_task(_run)
    return job.to_info()


@router.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise to_http_exception(JobNotFoundError(job_id))
    return job.to_info()


@router.get("/jobs", response_model=list[JobInfo])
async def list_jobs(limit: int = 30):
    return await job_manager.list_jobs(limit=min(limit, 100))


@router.delete("/jobs/{job_id}")
async def cancel_or_remove(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise to_http_exception(JobNotFoundError(job_id))
    await job_manager.cancel(job_id)
    return {"ok": True, "status": "cancelled"}


@router.get("/download/file/{job_id}")
async def download_file(job_id: str):
    """
    Serve completed file. Browser shows Save As dialog.
    Falls back to scanning downloads/ by job_id in filename if job expired from memory.
    """
    job = await job_manager.get_job(job_id)
    path: Path | None = None
    filename: str | None = None

    if job and job.status == JobStatus.COMPLETED and job.download_path and job.download_path.exists():
        path = job.download_path
        filename = job.filename or path.name
    else:
        # Fallback: look for files in downloads dir that contain job_id
        dl = settings.DOWNLOAD_DIR
        if dl.exists():
            for f in dl.iterdir():
                if f.is_file() and job_id in f.name:
                    path = f
                    filename = f.name
                    break
            # Also try exact match from history-style names if job has filename
            if not path and job and job.filename:
                candidate = dl / job.filename
                if candidate.exists():
                    path = candidate
                    filename = job.filename

    if not path or not path.exists():
        raise HTTPException(
            404,
            detail={
                "error": "file_missing",
                "message": "File not found. It may still be downloading, or was cleaned up. Check the downloads folder on your PC.",
            },
        )

    filename = filename or path.name
    # Safe header filename (ASCII fallback)
    safe_ascii = re.sub(r"[^\x20-\x7E]", "_", filename)
    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{filename}',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/files")
async def list_local_files():
    """List files currently in the downloads folder (always works even if jobs expired)."""
    dl = settings.DOWNLOAD_DIR
    items = []
    if dl.exists():
        for f in sorted(dl.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file():
                items.append({
                    "filename": f.name,
                    "size": f.stat().st_size,
                    "download_url": f"/api/files/{f.name}",
                })
    return {"items": items}


@router.get("/files/{filename}")
async def download_by_filename(filename: str):
    """Direct download by filename from downloads folder — triggers Save As."""
    # Prevent path traversal
    safe = Path(filename).name
    path = settings.DOWNLOAD_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(404, detail={"error": "file_missing", "message": "File not found"})
    safe_ascii = re.sub(r"[^\x20-\x7E]", "_", safe)
    return FileResponse(
        path=path,
        filename=safe,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_ascii}"',
            "Cache-Control": "no-cache",
        },
    )


@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete a file from downloads folder."""
    from pathlib import Path as P
    from app.core.config import settings
    from fastapi import HTTPException
    safe = P(filename).name
    path = settings.DOWNLOAD_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(404, detail={"error": "file_missing", "message": "File not found"})
    path.unlink()
    return {"ok": True, "deleted": safe}
