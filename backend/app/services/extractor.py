"""
Phase 3: yt-dlp URL Analyzer
"""
from __future__ import annotations
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

import yt_dlp

from app.core.exceptions import MediaAnalysisError
from app.models.schemas import MediaInfo, FormatInfo

logger = logging.getLogger("areebfetch.extractor")
_executor = ThreadPoolExecutor(max_workers=4)


def _format_duration(seconds) -> str | None:
    if seconds is None:
        return None
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class ExtractorService:
    def _base_opts(self) -> Dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "socket_timeout": 30,
            "retries": 3,
            "geo_bypass": True,
        }

    async def analyze(self, url: str) -> MediaInfo:
        loop = asyncio.get_event_loop()
        try:
            raw = await loop.run_in_executor(_executor, self._extract, url)
            return self._to_media_info(raw)
        except yt_dlp.utils.DownloadError as e:
            msg = str(e).split("\n")[0][:200]
            logger.warning(f"Analysis failed: {msg}")
            raise MediaAnalysisError(msg)
        except Exception as e:
            logger.exception("Unexpected analysis error")
            raise MediaAnalysisError(f"Analysis failed: {str(e)[:150]}")

    def _extract(self, url: str) -> Dict[str, Any]:
        opts = self._base_opts()
        opts["skip_download"] = True
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _to_media_info(self, raw: Dict[str, Any]) -> MediaInfo:
        formats: List[FormatInfo] = []
        heights: set[int] = set()

        for f in raw.get("formats") or []:
            if not f.get("format_id"):
                continue
            if f.get("vcodec") == "none" and f.get("acodec") == "none":
                continue

            height = f.get("height")
            if height:
                heights.add(int(height))

            quality_label = None
            if height:
                quality_label = f"{height}p"
            elif f.get("acodec") and f.get("acodec") != "none":
                abr = f.get("abr") or f.get("tbr")
                quality_label = f"{int(abr)}kbps" if abr else "audio"

            formats.append(FormatInfo(
                format_id=str(f["format_id"]),
                ext=f.get("ext") or "unknown",
                resolution=f.get("resolution") or (f"{f['width']}x{f['height']}" if f.get("width") else None),
                height=height,
                fps=f.get("fps"),
                vcodec=f.get("vcodec"),
                acodec=f.get("acodec"),
                filesize=f.get("filesize") or f.get("filesize_approx"),
                filesize_approx=f.get("filesize_approx"),
                tbr=f.get("tbr"),
                format_note=f.get("format_note"),
                quality_label=quality_label,
            ))

        # Sort: video by height desc, then audio
        formats.sort(key=lambda x: (
            0 if (x.vcodec and x.vcodec != "none") else 1,
            -(x.height or 0),
            -(x.tbr or 0),
        ))

        has_video = any(f.vcodec and f.vcodec != "none" for f in formats)
        has_audio = any(f.acodec and f.acodec != "none" for f in formats)

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
            description=(raw.get("description") or "")[:400] or None,
            view_count=raw.get("view_count"),
            formats=formats[:50],
            available_heights=sorted(heights, reverse=True),
            has_audio=has_audio,
            has_video=has_video,
        )


extractor_service = ExtractorService()