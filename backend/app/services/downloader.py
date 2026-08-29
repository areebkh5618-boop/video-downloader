"""
Video & Audio downloading with FFmpeg — fast concurrent fragments, 4K support
"""
from __future__ import annotations
import asyncio
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Dict, Any

import yt_dlp

from app.core.config import settings
from app.core.exceptions import DownloadError, FileTooLargeError
from app.models.schemas import JobStatus
from app.services.job_manager import Job, job_manager
from app.services.history import history_service
from app.utils.filenames import safe_filename, unique_path

logger = logging.getLogger("areebfetch.downloader")
_executor = ThreadPoolExecutor(max_workers=4)

QUALITY_MAP = {
    "best": None,
    "good": 1080,
    "normal": 720,
    "low": 480,
    "2160": 2160,
    "4k": 2160,
    "1440": 1440,
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
}


class DownloaderService:

    async def download(self, job: Job) -> Path:
        if not await job_manager.acquire():
            raise DownloadError("Too many concurrent downloads. Please wait.")

        try:
            job.update(status=JobStatus.DOWNLOADING, progress=1, message="Starting download…")
            work_dir = settings.TEMP_DIR / job.job_id
            work_dir.mkdir(parents=True, exist_ok=True)

            loop = asyncio.get_event_loop()
            final_path = await loop.run_in_executor(
                _executor, self._download_sync, job, work_dir
            )

            dest = unique_path(settings.DOWNLOAD_DIR, final_path.name)
            shutil.move(str(final_path), str(dest))
            shutil.rmtree(work_dir, ignore_errors=True)

            job.download_path = dest
            job.filename = dest.name
            job.update(
                status=JobStatus.COMPLETED,
                progress=100,
                message="Download complete",
                filename=dest.name,
            )
            try:
                history_service.add(
                    title=job.title or dest.name,
                    url=job.url,
                    status="completed",
                    thumbnail=job.thumbnail,
                    format=job.format,
                    quality=job.quality,
                    filename=dest.name,
                    filesize=dest.stat().st_size,
                    type=job.type,
                    job_id=job.job_id,
                )
            except Exception as e:
                logger.warning(f"History write failed: {e}")
            return dest

        except FileTooLargeError:
            raise
        except Exception as e:
            logger.exception(f"Download failed {job.job_id}")
            job.update(status=JobStatus.FAILED, error=str(e)[:300], message="Download failed")
            raise DownloadError(str(e)[:200])
        finally:
            await job_manager.release()

    def _download_sync(self, job: Job, work_dir: Path) -> Path:
        outtmpl = str(work_dir / "%(title).80B [%(id)s].%(ext)s")

        opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "outtmpl": outtmpl,
            "progress_hooks": [lambda d: self._progress_hook(d, job)],
            "noprogress": True,
            "retries": 5,
            "fragment_retries": 5,
            "socket_timeout": 30,
            "geo_bypass": True,
            # Speed: concurrent fragment downloads
            "concurrent_fragment_downloads": 8,
            "http_chunk_size": 10485760,
        }

        is_audio = job.type == "audio"
        fmt = (job.format or ("mp3" if is_audio else "mp4")).lower()
        quality = (job.quality or "best").lower()
        bitrate = str(job.extra.get("bitrate", "192"))

        if is_audio:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": fmt if fmt in ("mp3", "m4a", "wav", "aac", "flac", "opus") else "mp3",
                "preferredquality": bitrate,
            }]
        else:
            max_h = QUALITY_MAP.get(quality)
            if job.extra.get("format_id"):
                opts["format"] = job.extra["format_id"]
            elif max_h is None:
                # Best available including 4K/8K
                opts["format"] = "bestvideo*+bestaudio/best"
            else:
                opts["format"] = (
                    f"bestvideo[height<={max_h}]+bestaudio/"
                    f"best[height<={max_h}]/best"
                )
            if fmt in ("mp4", "mkv", "webm"):
                opts["merge_output_format"] = fmt

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(job.url, download=True)
            if not job.title:
                job.title = info.get("title")
            if not job.thumbnail:
                job.thumbnail = info.get("thumbnail")

            files = [p for p in work_dir.glob("*") if p.is_file()]
            if not files:
                raise DownloadError("No output file produced")

            final = max(files, key=lambda p: p.stat().st_size)
            size_mb = final.stat().st_size / (1024 * 1024)
            if size_mb > settings.MAX_FILE_SIZE_MB:
                final.unlink(missing_ok=True)
                raise FileTooLargeError(size_mb, settings.MAX_FILE_SIZE_MB)

            ext = final.suffix.lstrip(".") or fmt
            safe_name = safe_filename(info.get("title") or "download", ext)
            target = work_dir / safe_name
            if final != target:
                final.rename(target)
            return target

    def _progress_hook(self, d: Dict[str, Any], job: Job):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes") or 0
            progress = min((downloaded / total * 95) if total else 5, 95)
            job.update(
                status=JobStatus.DOWNLOADING,
                progress=progress,
                speed=d.get("_speed_str"),
                eta=d.get("_eta_str"),
                downloaded_bytes=downloaded,
                total_bytes=total,
                message=f"Downloading… {progress:.0f}%",
            )
        elif status == "finished":
            job.update(
                status=JobStatus.PROCESSING,
                progress=96,
                message="Processing / converting…",
            )


downloader_service = DownloaderService()
