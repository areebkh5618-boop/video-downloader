from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional

from app.services.pdf_tools import pdf_tools_service

router = APIRouter()


@router.post("/pdf/merge")
async def pdf_merge(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, detail={"error": "empty", "message": "Upload at least one PDF"})
    blobs, names = [], []
    for f in files:
        data = await f.read()
        if not data:
            continue
        blobs.append(data)
        names.append(f.filename or "file.pdf")
    if not blobs:
        raise HTTPException(400, detail={"error": "empty", "message": "No valid PDFs"})
    try:
        path, name, size = pdf_tools_service.merge(blobs, names)
    except Exception as e:
        raise HTTPException(500, detail={"error": "merge_failed", "message": str(e)[:200]})
    return {"filename": name, "size": size, "download_url": f"/api/files/{name}"}


@router.post("/pdf/split")
async def pdf_split(
    file: UploadFile = File(...),
    ranges: Optional[str] = Form(None),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, detail={"error": "empty", "message": "Empty PDF"})
    try:
        results = pdf_tools_service.split(data, ranges)
    except Exception as e:
        raise HTTPException(500, detail={"error": "split_failed", "message": str(e)[:200]})
    return {
        "items": [
            {"filename": n, "size": s, "download_url": f"/api/files/{n}"}
            for _, n, s in results
        ]
    }


@router.post("/pdf/compress")
async def pdf_compress(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, detail={"error": "empty", "message": "Empty PDF"})
    try:
        path, name, size = pdf_tools_service.compress(data)
    except Exception as e:
        raise HTTPException(500, detail={"error": "compress_failed", "message": str(e)[:200]})
    return {"filename": name, "size": size, "download_url": f"/api/files/{name}"}
