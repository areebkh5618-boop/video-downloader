"""PDF merge, split, compress"""
from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from pypdf import PdfReader, PdfWriter

from app.core.config import settings

logger = logging.getLogger("areebfetch.pdf")


class PdfToolsService:
    def merge(self, files: List[bytes], names: List[str]) -> tuple[Path, str, int]:
        writer = PdfWriter()
        for data in files:
            reader = PdfReader(io.BytesIO(data))
            for page in reader.pages:
                writer.add_page(page)
        out = settings.DOWNLOAD_DIR / f"merged_{uuid4().hex[:8]}.pdf"
        with open(out, "wb") as f:
            writer.write(f)
        return out, out.name, out.stat().st_size

    def split(self, data: bytes, ranges: Optional[str] = None) -> list[tuple[Path, str, int]]:
        """ranges e.g. '1-3,5,7-9' (1-based). If None, each page separate."""
        reader = PdfReader(io.BytesIO(data))
        n = len(reader.pages)
        results = []
        if not ranges:
            for i in range(n):
                w = PdfWriter()
                w.add_page(reader.pages[i])
                out = settings.DOWNLOAD_DIR / f"page_{i+1}_{uuid4().hex[:6]}.pdf"
                with open(out, "wb") as f:
                    w.write(f)
                results.append((out, out.name, out.stat().st_size))
            return results

        for part in ranges.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                start, end = int(a), int(b)
            else:
                start = end = int(part)
            start = max(1, start)
            end = min(n, end)
            w = PdfWriter()
            for i in range(start - 1, end):
                w.add_page(reader.pages[i])
            out = settings.DOWNLOAD_DIR / f"pages_{start}-{end}_{uuid4().hex[:6]}.pdf"
            with open(out, "wb") as f:
                w.write(f)
            results.append((out, out.name, out.stat().st_size))
        return results

    def compress(self, data: bytes) -> tuple[Path, str, int]:
        reader = PdfReader(io.BytesIO(data))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        try:
            writer.add_metadata({})
            for page in writer.pages:
                page.compress_content_streams()
        except Exception as e:
            logger.warning(f"compress stream note: {e}")
        out = settings.DOWNLOAD_DIR / f"compressed_{uuid4().hex[:8]}.pdf"
        with open(out, "wb") as f:
            writer.write(f)
        return out, out.name, out.stat().st_size


pdf_tools_service = PdfToolsService()
