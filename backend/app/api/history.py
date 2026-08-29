from fastapi import APIRouter, Query
from typing import Optional

from app.services.history import history_service
from app.core.exceptions import AreebFetchError, to_http_exception

router = APIRouter()


@router.get("/history")
async def list_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    status: Optional[str] = None,
):
    items = history_service.list(limit=limit, offset=offset, search=search, status=status)
    return {
        "items": items,
        "total": history_service.count(),
        "limit": limit,
        "offset": offset,
    }


@router.delete("/history/{entry_id}")
async def delete_history_item(entry_id: str):
    ok = history_service.delete(entry_id)
    if not ok:
        raise to_http_exception(AreebFetchError("History item not found", "not_found"))
    return {"ok": True}


@router.delete("/history")
async def clear_history():
    count = history_service.clear()
    return {"ok": True, "deleted": count}