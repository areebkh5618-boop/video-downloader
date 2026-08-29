from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import List, Union
import json


class Settings(BaseSettings):
    APP_NAME: str = "AreebFetch"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RATE_LIMIT: str = "30/minute"
    MAX_CONCURRENT_DOWNLOADS: int = 3
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMP_DIR: Path = BASE_DIR / "temp"
    DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
    LOG_DIR: Path = BASE_DIR / "logs"
    DATA_DIR: Path = BASE_DIR / "data"
    YTDLP_TIMEOUT: int = 300
    MAX_FILE_SIZE_MB: int = 4096
    CLEANUP_AFTER_HOURS: int = 24
    JOB_TTL_SECONDS: int = 86400

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_origins(self) -> List[str]:
        v = self.ALLOWED_ORIGINS
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return ["http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    for d in [s.TEMP_DIR, s.DOWNLOAD_DIR, s.LOG_DIR, s.DATA_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    return s


settings = get_settings()
