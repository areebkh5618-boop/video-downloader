"""CamScanner-style document scan: enhance + optional edge crop + PDF export"""
from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.core.config import settings

logger = logging.getLogger("areebfetch.scanner")

try:
    import cv2
    HAS_CV = True
except Exception:
    HAS_CV = False
    logger.warning("OpenCV not available — using Pillow-only scanner")


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def _four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1],
    ], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))


def _auto_detect_document(bgr: np.ndarray) -> Optional[np.ndarray]:
    if not HAS_CV:
        return None
    ratio = 500 / bgr.shape[0] if bgr.shape[0] > 500 else 1.0
    small = cv2.resize(bgr, None, fx=ratio, fy=ratio)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 50, 150)
    cnts, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:8]
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype("float32") / ratio
            return _four_point_transform(bgr, pts)
    return None


def _enhance_document(img: Image.Image, mode: str = "document") -> Image.Image:
    """mode: color | document | bw"""
    img = ImageOps.exif_transpose(img)
    if mode == "bw":
        img = img.convert("L")
        img = ImageOps.autocontrast(img, cutoff=2)
        img = img.point(lambda x: 255 if x > 160 else (0 if x < 100 else x))
        img = img.convert("RGB")
    elif mode == "document":
        img = img.convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.6)
        img = ImageEnhance.Sharpness(img).enhance(1.4)
        img = ImageEnhance.Brightness(img).enhance(1.05)
        # slight denoise
        img = img.filter(ImageFilter.MedianFilter(size=3))
    else:
        img = img.convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Sharpness(img).enhance(1.1)
    return img


class ScannerService:
    def scan_pages(
        self,
        pages: List[bytes],
        mode: str = "document",
        auto_crop: bool = True,
        export: str = "pdf",  # pdf | images
    ) -> Tuple[Path, str, int]:
        processed: List[Image.Image] = []
        for data in pages:
            img = Image.open(io.BytesIO(data))
            img = ImageOps.exif_transpose(img)
            if auto_crop and HAS_CV:
                arr = np.array(img.convert("RGB"))
                bgr = arr[:, :, ::-1].copy()
                warped = _auto_detect_document(bgr)
                if warped is not None and warped.size > 0:
                    img = Image.fromarray(warped[:, :, ::-1])
            img = _enhance_document(img, mode=mode)
            processed.append(img)

        if not processed:
            raise ValueError("No pages to process")

        if export == "images" and len(processed) == 1:
            out = settings.DOWNLOAD_DIR / f"scan_{uuid4().hex[:8]}.jpg"
            processed[0].save(out, "JPEG", quality=92, optimize=True)
            return out, out.name, out.stat().st_size

        # Multi-page or PDF export
        out = settings.DOWNLOAD_DIR / f"scan_{uuid4().hex[:8]}.pdf"
        rgb_pages = [p.convert("RGB") for p in processed]
        rgb_pages[0].save(
            out,
            "PDF",
            resolution=150.0,
            save_all=True,
            append_images=rgb_pages[1:] if len(rgb_pages) > 1 else [],
        )
        return out, out.name, out.stat().st_size


scanner_service = ScannerService()
