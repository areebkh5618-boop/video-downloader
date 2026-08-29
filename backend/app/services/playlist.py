"""
Phase 11: Playlist detection & extraction
"""
from __future__ import annotations
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional

import yt_dlp

from app.core.exceptions import MediaAnalysisError

logger = logging.getLogger("areebfetch.playlist")
_executor = ThreadPoolExecutor(max_workers=2)


class PlaylistService:
    def _base_opts(self) -> Dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "socket_timeout": 30,
            "retries": 2,
            "geo_bypass": True,
        }

    async def detect_and_extract(self, url: str) -> Optional[Dict[str, Any]]:
        """Return playlist info if URL is a playlist, else None."""
        loop = asyncio.get_event_loop()
        try:
            raw = await loop.run_in_executor(_executor, self._extract, url)
        except Exception as e:
            logger.warning(f"Playlist extract failed: {e}")
            return None

        if not raw:
            return None

        # Single video
        if raw.get("_type") != "playlist" and not raw.get("entries"):
            return None

        entries = []
        for i, e in enumerate(raw.get("entries") or []):
            if not e:
                continue
            entries.append({
                "id": str(e.get("id") or i),
                "title": e.get("title") or f"Video {i+1}",
                "url": e.get("url") or e.get("webpage_url") or "",
                "thumbnail": e.get("thumbnail"),
                "duration": e.get("duration"),
                "duration_string": self._fmt_duration(e.get("duration")),
                "uploader": e.get("uploader") or e.get("channel"),
            })

        if not entries:
            return None

        return {
            "is_playlist": True,
            "id": str(raw.get("id") or ""),
            "title": raw.get("title") or "Playlist",
            "uploader": raw.get("uploader") or raw.get("channel"),
            "thumbnail": raw.get("thumbnail"),
            "entry_count": len(entries),
            "entries": entries,
            "webpage_url": raw.get("webpage_url") or url,
        }

    def _extract(self, url: str) -> Dict[str, Any]:
        opts = self._base_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _fmt_duration(self, seconds) -> Optional[str]:
        if seconds is None:
            return None
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"


playlist_service = PlaylistService()