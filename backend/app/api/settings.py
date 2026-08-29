from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.settings_service import settings_service

router = APIRouter()


class SettingsUpdate(BaseModel):
    default_video_quality: Optional[str] = None
    default_video_format: Optional[str] = None
    default_audio_format: Optional[str] = None
    default_audio_bitrate: Optional[str] = None
    max_concurrent_downloads: Optional[int] = None
    save_thumbnails: Optional[bool] = None
    embed_metadata: Optional[bool] = None
    subtitle_preference: Optional[str] = None
    auto_start_download: Optional[bool] = None
    theme: Optional[str] = None


@router.get("/settings")
async def get_settings():
    return settings_service.get_all()


@router.put("/settings")
async def update_settings(body: SettingsUpdate):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    return settings_service.update(patch)