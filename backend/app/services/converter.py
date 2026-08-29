"""
Phase 5: FFmpeg processing (merge / convert)
"""
from __future__ import annotations
import asyncio
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("areebfetch.converter")


class ConverterService:
    def __init__(self):
        self.ffmpeg = shutil.which("ffmpeg")
        if not self.ffmpeg:
            logger.warning("FFmpeg not found on PATH")

    @property
    def available(self) -> bool:
        return bool(self.ffmpeg)

    async def merge_av(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """Merge separate video + audio streams into one container."""
        if not self.available:
            raise RuntimeError("FFmpeg is not installed")

        cmd = [
            self.ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            str(output_path),
        ]
        await self._run(cmd)
        return output_path

    async def convert_audio(
        self,
        input_path: Path,
        output_path: Path,
        codec: str = "mp3",
        bitrate: str = "192k",
    ) -> Path:
        if not self.available:
            raise RuntimeError("FFmpeg is not installed")

        codec_map = {
            "mp3": "libmp3lame",
            "m4a": "aac",
            "aac": "aac",
            "wav": "pcm_s16le",
            "flac": "flac",
            "opus": "libopus",
        }
        acodec = codec_map.get(codec, "libmp3lame")

        cmd = [
            self.ffmpeg, "-y",
            "-i", str(input_path),
            "-vn",
            "-acodec", acodec,
        ]
        if codec not in ("wav", "flac"):
            cmd.extend(["-b:a", bitrate])
        cmd.append(str(output_path))

        await self._run(cmd)
        return output_path

    async def _run(self, cmd: list[str]) -> None:
        logger.info(f"FFmpeg: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode(errors="ignore")[-500:]
            logger.error(f"FFmpeg failed: {err}")
            raise RuntimeError(f"FFmpeg processing failed: {err[:200]}")


converter_service = ConverterService()