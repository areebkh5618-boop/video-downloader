import re
from pathlib import Path


def safe_filename(title: str, ext: str, max_len: int = 100) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title or "download")
    name = re.sub(r"\s+", " ", name).strip()
    name = name[:max_len] or "download"
    ext = ext.lstrip(".").lower() or "mp4"
    return f"{name}.{ext}"


def unique_path(directory: Path, filename: str) -> Path:
    target = directory / filename
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1