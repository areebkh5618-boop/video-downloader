"""
Phase 13: Settings (JSON file based)
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger("areebfetch.settings")

DEFAULTS: Dict[str, Any] = {
    "default_video_quality": "best",
    "default_video_format": "mp4",
    "default_audio_format": "mp3",
    "default_audio_bitrate": "192",
    "max_concurrent_downloads": 3,
    "save_thumbnails": False,
    "embed_metadata": True,
    "subtitle_preference": "none",          # none | original | lang code
    "auto_start_download": False,
    "theme": "system",                      # light | dark | system
}


class SettingsService:
    def __init__(self):
        self.path = settings.DATA_DIR / "settings.json"
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {**DEFAULTS, **data}
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")
        return dict(DEFAULTS)

    def _save(self):
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get_all(self) -> Dict[str, Any]:
        return dict(self._data)

    def update(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in patch.items():
            if k in DEFAULTS:
                self._data[k] = v
        self._save()
        return self.get_all()

    def get(self, key: str, default=None):
        return self._data.get(key, default)


settings_service = SettingsService()