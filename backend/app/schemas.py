"""
app/schemas.py
All Pydantic models for request validation and response serialisation.
"""
from typing import Optional
from pydantic import BaseModel, field_validator
import re


# ── Shared URL validator ────────────────────────────────────────────────────
YOUTUBE_PATTERNS = [
    r"youtube\.com/watch\?.*v=[\w-]{11}",
    r"youtu\.be/[\w-]{11}",
    r"youtube\.com/shorts/[\w-]{11}",
    r"youtube\.com/embed/[\w-]{11}",
    r"youtube\.com/live/[\w-]{11}",
    r"m\.youtube\.com/watch\?.*v=[\w-]{11}",
]

def _validate_yt_url(url: str) -> str:
    url = url.strip()
    if not any(re.search(p, url) for p in YOUTUBE_PATTERNS):
        raise ValueError(
            "URL does not appear to be a valid public YouTube video link. "
            "Supported formats: youtube.com/watch?v=…, youtu.be/…, youtube.com/shorts/…"
        )
    return url


# ── Request models ──────────────────────────────────────────────────────────
class FetchInfoRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_yt_url(v)


VALID_MP3_QUALITIES = {"70k", "128k", "160k", "320k", "620k"}
VALID_MP4_QUALITIES = {
    "144p", "240p", "360p", "480p", "720p",
    "1080p", "1440p", "2160p", "4320p",
    "1080p-hdr", "1440p-hdr", "4k-hdr", "8k-hdr",
}

class DownloadRequest(BaseModel):
    url: str
    mode: str       # "mp3" | "mp4"
    quality: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _validate_yt_url(v)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ("mp3", "mp4"):
            raise ValueError("mode must be 'mp3' or 'mp4'")
        return v

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: str, info) -> str:
        # Cross-field: we validate against mode after both are set
        # Basic check here; full check done in the router
        all_valid = VALID_MP3_QUALITIES | VALID_MP4_QUALITIES
        if v not in all_valid:
            raise ValueError(
                f"quality '{v}' is not supported. "
                f"MP3 options: {sorted(VALID_MP3_QUALITIES)}. "
                f"MP4 options: {sorted(VALID_MP4_QUALITIES)}."
            )
        return v


# ── Response models ─────────────────────────────────────────────────────────
class VideoInfoResponse(BaseModel):
    title: str
    duration_seconds: int
    duration_str: str
    thumbnail: Optional[str] = None
    uploader: Optional[str] = None
    channel_url: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    upload_date: Optional[str] = None
    description_snippet: Optional[str] = None
    is_live: bool = False
    available_formats: list[str] = []


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    yt_dlp_version: str
