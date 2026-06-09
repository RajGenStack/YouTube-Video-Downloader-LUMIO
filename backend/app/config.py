"""
app/config.py
Centralised configuration loaded from environment variables.
All secrets / tunables live here — never hard-coded elsewhere.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────
    APP_NAME: str = "Lumio API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"          # production | staging | development

    # ── CORS ───────────────────────────────────────────────
    # Comma-separated list of allowed frontend origins
    ALLOWED_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── Rate limiting ──────────────────────────────────────
    RATE_LIMIT_FETCH: str = "30/minute"      # per-IP for /api/fetch-info
    RATE_LIMIT_DOWNLOAD: str = "10/minute"   # per-IP for /api/download

    # ── Download settings ──────────────────────────────────
    MAX_VIDEO_DURATION_SECONDS: int = 10800  # 3 hours – refuse longer videos
    DOWNLOAD_TIMEOUT_SECONDS: int = 600      # 10 min – kill stalled yt-dlp
    TMP_DIR: str = "/tmp/lumio_downloads"
    CLEANUP_AFTER_SECONDS: int = 300         # delete tmp files after 5 min

    # ── yt-dlp cookies (optional, helps with age-restricted) ──
    COOKIES_FILE: str = ""                   # absolute path to cookies.txt

    # ── Logging ────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
