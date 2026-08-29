"""
yt-dlp + FFmpeg service.
Phase 6: robust error handling, size limits, safe temp dirs, progress hooks.
"""
from __future__ import annotations
import asyncio
import json
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from app.core.config import settings
from app.core.exceptions import MediaAnalysisError, DownloadError, FileTooLargeError
from app.models.schemas import MediaInfo, FormatInfo, JobStatus
from app.services.job_manager import Job, job_manager

logger = logging.getLogger("areebfetch.media")

# Shared thread pool for blocking yt-dlp calls
_executor = ThreadPoolExecutor(max_workers=4)


def _human_size(n: Optional[int]) -> Optional[str]:
    if n is None:
        return None
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _format_duration(seconds: Optional[float]) -> Optional[str]:
    if seconds is None:
        return None
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _safe_filename(title: str, max_len: int = 80) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title).strip()
    name = re.sub(r"\s+", " ", name)
    return name[:max_len] or "download"


class MediaService:

    @staticmethod
    def _base_ydl_opts() -> Dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "ignoreerrors": False,
            "geo_bypass": True,
            "nocheckcertificate": False,
        }

    async def analyze(self, url: str) -> MediaInfo:
        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(_executor, self._extract_info, url)
            return self._to_media_info(info)
        except yt_dlp.utils.DownloadError as e:
            logger.warning(f"yt-dlp analysis failed for {url}: {e}")
            raise MediaAnalysisError(str(e).split("\n")[0][:200])
        except Exception as e:
            logger.exception("Unexpected analysis error")
            raise MediaAnalysisError(f"Analysis failed: {str(e)[:150]}")

    def _extract_info(self, url: str) -> Dict[str, Any]:
        opts = self._base_ydl_opts()
        opts["skip_download"] = True
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _to_media_info(self, raw: Dict[str, Any]) -> MediaInfo:
        formats = []
        for f in raw.get("formats") or []:
            if not f.get("format_id"):
                continue
            # Skip storyboard / pure images
            if f.get("vcodec") == "none" and f.get("acodec") == "none":
                continue
            fmt = FormatInfo(
                format_id=str(f["format_id"]),
                ext=f.get("ext") or "unknown",
                resolution=f.get("resolution") or (f"{f['width']}x{f['height']}" if f.get("width") else None),
                fps=f.get("fps"),
                vcodec=f.get("vcodec"),
                acodec=f.get("acodec"),
                filesize=f.get("filesize") or f.get("filesize_approx"),
                filesize_approx=f.get("filesize_approx"),
                tbr=f.get("tbr"),
                format_note=f.get("format_note"),
                quality=self._quality_label(f),
            )
            formats.append(fmt)

        # Sort: video first by height desc, then audio
        formats.sort(key=lambda x: (
            0 if x.vcodec and x.vcodec != "none" else 1,
            -(int(x.resolution.split("x")[1]) if x.resolution and "x" in x.resolution else 0),
            -(x.tbr or 0)
        ))

        best_video = next((f for f in formats if f.vcodec and f.vcodec != "none"), None)
        best_audio = next((f for f in formats if f.acodec and f.acodec != "none" and (not f.vcodec or f.vcodec == "none")), None)

        return MediaInfo(
            id=str(raw.get("id") or ""),
            title=raw.get("title") or "Unknown Title",
            thumbnail=raw.get("thumbnail"),
            duration=raw.get("duration"),
            duration_string=_format_duration(raw.get("duration")),
            uploader=raw.get("uploader") or raw.get("channel"),
            uploader_url=raw.get("uploader_url") or raw.get("channel_url"),
            webpage_url=raw.get("webpage_url") or raw.get("original_url") or "",
            extractor=raw.get("extractor") or raw.get("ie_key") or "unknown",
            description=(raw.get("description") or "")[:500] or None,
            view_count=raw.get("view_count"),
            like_count=raw.get("like_count"),
            upload_date=raw.get("upload_date"),
            formats=formats[:40],  # limit response size
            best_video=best_video,
            best_audio=best_audio,
        )

    def _quality_label(self, f: Dict) -> str:
        if f.get("vcodec") and f.get("vcodec") != "none":
            height = f.get("height")
            if height:
                return f"{height}p"
            return f.get("format_note") or f.get("resolution") or "video"
        if f.get("acodec") and f.get("acodec") != "none":
            abr = f.get("abr") or f.get("tbr")
            if abr:
                return f"{int(abr)}kbps audio"
            return "audio"
        return f.get("format_note") or "unknown"

    async def download(
        self,
        job: Job,
        format_id: Optional[str] = None,
        audio_only: bool = False,
        audio_format: str = "mp3",
        video_quality: Optional[str] = None,
    ) -> Path:
        if not await job_manager.acquire_download_slot():
            raise DownloadError("Too many concurrent downloads. Please try again shortly.")

        try:
            job.update(status=JobStatus.DOWNLOADING, progress=0, message="Starting download…")

            work_dir = settings.TEMP_DIR / job.job_id
            work_dir.mkdir(parents=True, exist_ok=True)

            loop = asyncio.get_event_loop()
            final_path = await loop.run_in_executor(
                _executor,
                self._download_sync,
                job,
                work_dir,
                format_id,
                audio_only,
                audio_format,
                video_quality,
            )

            # Move to permanent downloads dir
            dest = settings.DOWNLOAD_DIR / final_path.name
            if dest.exists():
                dest.unlink()
            shutil.move(str(final_path), str(dest))

            # Cleanup work dir
            shutil.rmtree(work_dir, ignore_errors=True)

            job.download_path = dest
            job.filename = dest.name
            job.update(
                status=JobStatus.COMPLETED,
                progress=100,
                message="Download complete",
                filename=dest.name,
            )
            return dest

        except FileTooLargeError:
            raise
        except Exception as e:
            logger.exception(f"Download failed for job {job.job_id}")
            job.update(status=JobStatus.FAILED, error=str(e)[:300], message="Download failed")
            raise DownloadError(str(e)[:200])
        finally:
            await job_manager.release_download_slot()

    def _download_sync(
        self,
        job: Job,
        work_dir: Path,
        format_id: Optional[str],
        audio_only: bool,
        audio_format: str,
        video_quality: Optional[str],
    ) -> Path:
        outtmpl = str(work_dir / "%(title).80s [%(id)s].%(ext)s")

        opts = self._base_ydl_opts()
        opts.update({
            "outtmpl": outtmpl,
            "progress_hooks": [lambda d: self._progress_hook(d, job)],
            "noprogress": True,
        })

        if audio_only:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "192",
            }]
        elif format_id:
            opts["format"] = format_id
        elif video_quality and video_quality != "best":
            # e.g. 1080, 720 …
            height = video_quality.rstrip("p")
            opts["format"] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
        else:
            opts["format"] = "bestvideo+bestaudio/best"

        # Merge when needed
        opts["merge_output_format"] = "mp4"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(job.url, download=True)
            # Find the actual output file
            requested = ydl.prepare_filename(info)
            # After post-processing the extension may change
            possible = list(work_dir.glob("*"))
            if not possible:
                raise DownloadError("No output file produced")
            # Prefer the largest file (final merged/converted)
            final = max(possible, key=lambda p: p.stat().st_size)

            size_mb = final.stat().st_size / (1024 * 1024)
            if size_mb > settings.MAX_FILE_SIZE_MB:
                final.unlink(missing_ok=True)
                raise FileTooLargeError(size_mb, settings.MAX_FILE_SIZE_MB)

            # Sanitize final name
            safe_title = _safe_filename(info.get("title") or "download")
            new_name = f"{safe_title}.{final.suffix.lstrip('.')}"
            target = work_dir / new_name
            if final != target:
                final.rename(target)
            return target

    def _progress_hook(self, d: Dict[str, Any], job: Job):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes") or 0
            progress = (downloaded / total * 100) if total else 0
            speed = d.get("_speed_str")
            eta = d.get("_eta_str")
            job.update(
                status=JobStatus.DOWNLOADING,
                progress=min(progress, 99),
                speed=speed,
                eta=eta,
                downloaded_bytes=downloaded,
                total_bytes=total,
                message=f"Downloading… {progress:.1f}%",
            )
        elif d["status"] == "finished":
            job.update(
                status=JobStatus.PROCESSING,
                progress=95,
                message="Processing / converting…",
            )


media_service = MediaService()