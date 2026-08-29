from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import validate_url
from app.core.exceptions import AreebFetchError, to_http_exception
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.extractor import extractor_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit(settings.RATE_LIMIT)
async def analyze(request: Request, body: AnalyzeRequest):
    try:
        url = validate_url(body.url)
        info = await extractor_service.analyze(url)
        return AnalyzeResponse(data=info)
    except AreebFetchError as e:
        raise to_http_exception(e)