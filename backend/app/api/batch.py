"""
Phase 12: Batch URL downloading
"""
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import validate_url
from app.core.exceptions import AreebFetchError, to_http_exception
from app.models.schemas import JobInfo, DownloadRequest
from app.services.job_manager import job_manager
from app.services.downloader import downloader_service
from app.services.extractor import extractor_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class BatchRequest(BaseModel):
    urls: List[str]
    type: str = "video"
    quality: Optional[str] = "best"
    format: Optional[str] = "mp4"
    bitrate: Optional[str] = "192"


@router.post("/batch")
@limiter.limit("5/minute")
async def batch_download(request: Request, body: BatchRequest, background_tasks: BackgroundTasks):
    if not body.urls:
        raise HTTPException(400, detail={"error": "empty", "message": "No URLs provided"})
    if len(body.urls) > 30:
        raise HTTPException(400, detail={"error": "too_many", "message": "Maximum 30 URLs per batch"})

    jobs: List[JobInfo] = []
    errors: List[dict] = []

    for raw_url in body.urls:
        raw_url = raw_url.strip()
        if not raw_url:
            continue
        try:
            url = validate_url(raw_url)
        except AreebFetchError as e:
            errors.append({"url": raw_url, "error": e.message})
            continue

        job = await job_manager.create_job(
            url,
            type=body.type,
            quality=body.quality,
            format=body.format,
            bitrate=body.bitrate,
        )
        jobs.append(job.to_info())

        async def _run(j=job, u=url):
            try:
                try:
                    info = await extractor_service.analyze(u)
                    j.title = info.title
                    j.thumbnail = info.thumbnail
                except Exception:
                    pass
                await downloader_service.download(j)
            except Exception as e:
                from app.models.schemas import JobStatus
                if j.status not in (JobStatus.FAILED, JobStatus.COMPLETED, JobStatus.CANCELLED):
                    j.update(status=JobStatus.FAILED, error=str(e)[:300])

        background_tasks.add_task(_run)

    return {
        "jobs": jobs,
        "queued": len(jobs),
        "errors": errors,
    }