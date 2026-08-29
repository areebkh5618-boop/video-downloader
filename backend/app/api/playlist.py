from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import validate_url
from app.core.exceptions import AreebFetchError, to_http_exception
from app.services.playlist import playlist_service
from app.services.extractor import extractor_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class PlaylistRequest(BaseModel):
    url: str


@router.post("/playlist")
@limiter.limit(settings.RATE_LIMIT)
async def analyze_playlist(request: Request, body: PlaylistRequest):
    try:
        url = validate_url(body.url)
    except AreebFetchError as e:
        raise to_http_exception(e)

    # First try playlist detection
    playlist = await playlist_service.detect_and_extract(url)
    if playlist:
        return {"is_playlist": True, "data": playlist}

    # Fallback to single media
    try:
        info = await extractor_service.analyze(url)
        return {"is_playlist": False, "data": info}
    except AreebFetchError as e:
        raise to_http_exception(e)