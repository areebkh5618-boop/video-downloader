from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional

from app.services.scanner import scanner_service

router = APIRouter()


@router.post("/scanner/scan")
async def scan_document(
    files: List[UploadFile] = File(...),
    mode: str = Form("document"),  # color | document | bw
    auto_crop: bool = Form(True),
    export: str = Form("pdf"),  # pdf | images
):
    if not files:
        raise HTTPException(400, detail={"error": "empty", "message": "Upload at least one page image"})
    pages = []
    for f in files:
        if f.content_type and not f.content_type.startswith("image/"):
            continue
        data = await f.read()
        if data:
            pages.append(data)
    if not pages:
        raise HTTPException(400, detail={"error": "empty", "message": "No valid images"})
    if len(pages) > 30:
        raise HTTPException(400, detail={"error": "too_many", "message": "Max 30 pages per scan"})
    try:
        path, name, size = scanner_service.scan_pages(
            pages=pages,
            mode=mode if mode in ("color", "document", "bw") else "document",
            auto_crop=auto_crop,
            export=export if export in ("pdf", "images") else "pdf",
        )
    except Exception as e:
        raise HTTPException(500, detail={"error": "scan_failed", "message": str(e)[:200]})
    return {"filename": name, "size": size, "download_url": f"/api/files/{name}", "pages": len(pages)}
