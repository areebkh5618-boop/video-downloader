from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import re

from app.services.image_tools import image_tools_service

router = APIRouter()


@router.post("/images/process")
async def process_image(
    file: UploadFile = File(...),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    quality: int = Form(85),
    format: str = Form("JPEG"),
    keep_aspect: bool = Form(True),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, detail={"error": "invalid", "message": "Please upload an image file"})
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(400, detail={"error": "too_large", "message": "Max 50 MB image"})
    try:
        path, name, size = image_tools_service.process(
            data=data,
            original_name=file.filename or "image.jpg",
            width=width,
            height=height,
            quality=quality,
            format=format,
            keep_aspect=keep_aspect,
        )
    except Exception as e:
        raise HTTPException(500, detail={"error": "process_failed", "message": str(e)[:200]})

    return {
        "filename": name,
        "size": size,
        "download_url": f"/api/files/{name}",
    }
