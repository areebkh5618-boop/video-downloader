from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class JobStatus(str, Enum):
    WAITING = "waiting"
    ANALYZING = "analyzing"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FormatInfo(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    filesize_approx: Optional[int] = None
    tbr: Optional[float] = None
    format_note: Optional[str] = None
    quality_label: Optional[str] = None


class MediaInfo(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[float] = None
    duration_string: Optional[str] = None
    uploader: Optional[str] = None
    uploader_url: Optional[str] = None
    webpage_url: str
    extractor: str
    description: Optional[str] = None
    view_count: Optional[int] = None
    formats: List[FormatInfo] = []
    available_heights: List[int] = []
    has_audio: bool = True
    has_video: bool = True


class AnalyzeRequest(BaseModel):
    url: str


class AnalyzeResponse(BaseModel):
    success: bool = True
    data: MediaInfo


class DownloadRequest(BaseModel):
    url: str
    type: str = "video"
    quality: Optional[str] = "best"
    format: Optional[str] = "mp4"
    bitrate: Optional[str] = "192"
    format_id: Optional[str] = None
    save_thumbnail: bool = False


class ProgressUpdate(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = Field(ge=0, le=100)
    speed: Optional[str] = None
    eta: Optional[str] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    message: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class JobInfo(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    url: str
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    type: str = "video"
    quality: Optional[str] = None
    format: Optional[str] = None
    progress: float = 0.0
    download_url: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None
    expires_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float
    active_jobs: int
    disk_usage_mb: float
    yt_dlp_version: Optional[str] = None
    ffmpeg_available: bool