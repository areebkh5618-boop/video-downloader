"""Image compress & resize using Pillow"""
from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from PIL import Image

from app.core.config import settings

logger = logging.getLogger("areebfetch.image")


class ImageToolsService:
    def process(
        self,
        data: bytes,
        original_name: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: int = 85,
        format: str = "JPEG",
        keep_aspect: bool = True,
    ) -> Tuple[Path, str, int]:
        fmt = format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        if fmt not in ("JPEG", "PNG", "WEBP"):
            fmt = "JPEG"

        img = Image.open(io.BytesIO(data))
        # Convert palette / RGBA for JPEG
        if fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode == "P":
            img = img.convert("RGBA")

        if width or height:
            orig_w, orig_h = img.size
            if keep_aspect:
                if width and height:
                    ratio = min(width / orig_w, height / orig_h)
                    new_size = (max(1, int(orig_w * ratio)), max(1, int(orig_h * ratio)))
                elif width:
                    ratio = width / orig_w
                    new_size = (width, max(1, int(orig_h * ratio)))
                else:
                    ratio = height / orig_h
                    new_size = (max(1, int(orig_w * ratio)), height)
            else:
                new_size = (width or orig_w, height or orig_h)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        quality = max(1, min(100, quality))
        stem = Path(original_name).stem[:60] or "image"
        ext = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[fmt]
        out_name = f"{stem}_processed_{uuid4().hex[:8]}.{ext}"
        out_path = settings.DOWNLOAD_DIR / out_name

        save_kwargs = {}
        if fmt in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        if fmt == "PNG":
            save_kwargs["optimize"] = True

        img.save(out_path, format=fmt, **save_kwargs)
        return out_path, out_name, out_path.stat().st_size


image_tools_service = ImageToolsService()
