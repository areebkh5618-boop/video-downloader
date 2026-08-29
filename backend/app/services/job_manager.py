from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from pathlib import Path
import shutil
import logging

from app.core.config import settings
from app.models.schemas import JobStatus, JobInfo, ProgressUpdate

logger = logging.getLogger("areebfetch.jobs")


class Job:
    def __init__(self, url: str, **kwargs):
        self.job_id = str(uuid.uuid4())
        self.url = url
        self.status = JobStatus.WAITING
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.progress = 0.0
        self.title: Optional[str] = None
        self.thumbnail: Optional[str] = None
        self.type: str = kwargs.get("type", "video")
        self.quality: Optional[str] = kwargs.get("quality")
        self.format: Optional[str] = kwargs.get("format")
        self.filename: Optional[str] = None
        self.download_path: Optional[Path] = None
        self.error: Optional[str] = None
        self.speed: Optional[str] = None
        self.eta: Optional[str] = None
        self.downloaded_bytes: Optional[int] = None
        self.total_bytes: Optional[int] = None
        self.message: Optional[str] = None
        self.extra = kwargs
        self._subscribers: list[Callable] = []

    def to_info(self) -> JobInfo:
        expires = self.created_at + timedelta(seconds=settings.JOB_TTL_SECONDS)
        download_url = None
        if self.status == JobStatus.COMPLETED and self.filename:
            download_url = f"/api/download/file/{self.job_id}"
        return JobInfo(
            job_id=self.job_id,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            url=self.url,
            title=self.title,
            thumbnail=self.thumbnail,
            type=self.type,
            quality=self.quality,
            format=self.format,
            progress=self.progress,
            download_url=download_url,
            filename=self.filename,
            error=self.error,
            expires_at=expires,
        )

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.updated_at = datetime.utcnow()
        update = ProgressUpdate(
            job_id=self.job_id,
            status=self.status,
            progress=self.progress,
            speed=self.speed,
            eta=self.eta,
            downloaded_bytes=self.downloaded_bytes,
            total_bytes=self.total_bytes,
            message=self.message,
            filename=self.filename,
            error=self.error,
        )
        for cb in list(self._subscribers):
            try:
                cb(update)
            except Exception as e:
                logger.warning(f"Subscriber error: {e}")

    def subscribe(self, callback: Callable):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        if callback in self._subscribers:
            self._subscribers.remove(callback)


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._active = 0
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("JobManager started")

    async def stop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.cleanup_expired(force=True)

    async def create_job(self, url: str, **kwargs) -> Job:
        async with self._lock:
            job = Job(url, **kwargs)
            self._jobs[job.job_id] = job
            return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    async def list_jobs(self, limit: int = 50) -> list[JobInfo]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return [j.to_info() for j in jobs[:limit]]

    async def can_start(self) -> bool:
        async with self._lock:
            return self._active < settings.MAX_CONCURRENT_DOWNLOADS

    async def acquire(self) -> bool:
        async with self._lock:
            if self._active >= settings.MAX_CONCURRENT_DOWNLOADS:
                return False
            self._active += 1
            return True

    async def release(self):
        async with self._lock:
            self._active = max(0, self._active - 1)

    async def cancel(self, job_id: str) -> bool:
        job = await self.get_job(job_id)
        if not job:
            return False
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            return False
        job.update(status=JobStatus.CANCELLED, message="Cancelled by user")
        return True

    async def cleanup_expired(self, force: bool = False):
        now = datetime.utcnow()
        ttl = timedelta(seconds=settings.JOB_TTL_SECONDS)
        to_remove = []
        async with self._lock:
            for jid, job in self._jobs.items():
                expired = (now - job.created_at) > ttl
                finished = job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
                if force or (expired and finished) or (expired and not finished):
                    to_remove.append(jid)
            for jid in to_remove:
                job = self._jobs.pop(jid, None)
                if job and job.download_path and job.download_path.exists():
                    try:
                        if job.download_path.is_file():
                            job.download_path.unlink()
                        else:
                            shutil.rmtree(job.download_path, ignore_errors=True)
                    except Exception as e:
                        logger.warning(f"Cleanup error {jid}: {e}")

    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.sleep(300)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")


job_manager = JobManager()