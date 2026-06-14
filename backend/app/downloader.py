"""
app/downloader.py
Core business logic: wraps yt-dlp and FFmpeg.
All heavy I/O runs in a thread pool via asyncio.to_thread() so the
FastAPI event loop is never blocked.
"""
import asyncio
import os
import re
import uuid
from pathlib import Path
from typing import Optional

import yt_dlp

from app.config import get_settings
from app.logger import logger
from app.schemas import VideoInfoResponse

settings = get_settings()

# ── Ensure temp directory exists ────────────────────────────────────────────
TMP_DIR = Path(settings.TMP_DIR)
TMP_DIR.mkdir(parents=True, exist_ok=True)


# ── Format maps ─────────────────────────────────────────────────────────────
AUDIO_BITRATE_MAP: dict[str, str] = {
    "70k":  "70",
    "128k": "128",
    "160k": "160",
    "320k": "320",
}

VIDEO_FORMAT_MAP: dict[str, str] = {
    "144p":      "bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=144]+bestaudio/best[height<=144]",
    "240p":      "bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=240]+bestaudio/best[height<=240]",
    "360p":      "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]",
    "480p":      "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
    "720p":      "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080p":     "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "1440p":     "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "2160p":     "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "4320p":     "bestvideo[height<=4320][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=4320]+bestaudio/best[height<=4320]",
    # HDR – prefer HDR codec, fallback to SDR
    "1080p-hdr": "bestvideo[height<=1080][dynamic_range=HDR]+bestaudio/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "1440p-hdr": "bestvideo[height<=1440][dynamic_range=HDR]+bestaudio/bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "4k-hdr":    "bestvideo[height<=2160][dynamic_range=HDR]+bestaudio/bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "8k-hdr":    "bestvideo[height<=4320][dynamic_range=HDR]+bestaudio/bestvideo[height<=4320]+bestaudio/best[height<=4320]",
}

# Heights exposed per quality key (used to list available formats)
QUALITY_HEIGHT_MAP: dict[str, int] = {
    "144p": 144, "240p": 240, "360p": 360, "480p": 480,
    "720p": 720, "1080p": 1080, "1440p": 1440,
    "2160p": 2160, "4320p": 4320,
}


# ── Helpers ─────────────────────────────────────────────────────────────────
def seconds_to_str(secs: int) -> str:
    h, rem = divmod(int(secs), 3600)
    m, s   = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def safe_filename(name: str, ext: str) -> str:
    """Strip filesystem-unsafe characters and truncate."""
    clean = re.sub(r'[\\/*?:"<>|]', "-", name).strip()
    return f"{clean[:180]}.{ext}"


def _base_ydl_opts() -> dict:
    """Common yt-dlp options for every call."""
    opts: dict = {
        "quiet":       True,
        "no_warnings": True,
        "noprogress":  True,
        "noplaylist":  True,           # single video only
        "socket_timeout": 30,
        "retries":     3,
        "fragment_retries": 3,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    }
    if settings.COOKIES_FILE and os.path.isfile(settings.COOKIES_FILE):
        try:
            # Safely verify the file is readable and not a directory
            with open(settings.COOKIES_FILE, "r") as f:
                f.read(1)
            opts["cookiefile"] = settings.COOKIES_FILE
        except Exception as e:
            logger.error(f"Cannot read cookies file at {settings.COOKIES_FILE}: {e}")
    if settings.PROXY_URL:
        opts["proxy"] = settings.PROXY_URL
    return opts


def _get_available_mp4_qualities(formats: list) -> list[str]:
    """Return which of our named video qualities are actually in the stream list."""
    available = []
    
    # Regular resolutions
    heights = {f.get("height") for f in formats if f.get("height")}
    for key, h in QUALITY_HEIGHT_MAP.items():
        if any(fh >= h for fh in heights):
            available.append(key)
            
    # HDR resolutions
    hdr_heights = {
        f.get("height")
        for f in formats
        if f.get("height") and "HDR" in str(f.get("dynamic_range") or "")
    }
    if any(h >= 1080 for h in hdr_heights):
        available.append("1080p-hdr")
    if any(h >= 1440 for h in hdr_heights):
        available.append("1440p-hdr")
    if any(h >= 2160 for h in hdr_heights):
        available.append("4k-hdr")
    if any(h >= 4320 for h in hdr_heights):
        available.append("8k-hdr")
        
    return available


# ── Public API ───────────────────────────────────────────────────────────────
async def fetch_video_info(url: str) -> VideoInfoResponse:
    """
    Extract video metadata without downloading.
    Raises ValueError on bad URLs / private videos.
    """
    ydl_opts = {**_base_ydl_opts(), "skip_download": True}

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        info = await asyncio.wait_for(
            asyncio.to_thread(_run),
            timeout=settings.DOWNLOAD_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise ValueError("Request timed out while fetching video info. Try again.")
    except yt_dlp.utils.DownloadError as exc:
        raise ValueError(f"Could not fetch video: {exc}") from exc

    duration = int(info.get("duration") or 0)

    if duration > settings.MAX_VIDEO_DURATION_SECONDS:
        raise ValueError(
            f"Video is too long ({seconds_to_str(duration)}). "
            f"Maximum allowed duration is {seconds_to_str(settings.MAX_VIDEO_DURATION_SECONDS)}."
        )

    desc = info.get("description") or ""
    snippet = desc[:200].replace("\n", " ") + ("…" if len(desc) > 200 else "")

    raw_formats = info.get("formats") or []
    avail = _get_available_mp4_qualities(raw_formats)

    return VideoInfoResponse(
        title=info.get("title") or "Unknown Title",
        duration_seconds=duration,
        duration_str=seconds_to_str(duration),
        thumbnail=info.get("thumbnail"),
        uploader=info.get("uploader"),
        channel_url=info.get("channel_url"),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        upload_date=info.get("upload_date"),
        description_snippet=snippet,
        is_live=bool(info.get("is_live")),
        available_formats=avail,
    )


class DownloadResult:
    """Container returned from download_media()."""
    __slots__ = ("file_path", "filename", "media_type")

    def __init__(self, file_path: str, filename: str, media_type: str):
        self.file_path  = file_path
        self.filename   = filename
        self.media_type = media_type


async def download_media(url: str, mode: str, quality: str) -> DownloadResult:
    """
    Download and process a YouTube video.
    Returns a DownloadResult with the path to the finished file.
    Caller is responsible for scheduling file deletion.
    """
    job_id   = uuid.uuid4().hex
    out_tmpl = str(TMP_DIR / f"{job_id}.%(ext)s")

    # ── Build yt-dlp options ─────────────────────────────────────────────
    if mode == "mp3":
        abr = AUDIO_BITRATE_MAP.get(quality, "192")
        ydl_opts = {
            **_base_ydl_opts(),
            "format":    "bestaudio/best",
            "outtmpl":   out_tmpl,
            "postprocessors": [
                {
                    "key":              "FFmpegExtractAudio",
                    "preferredcodec":   "mp3",
                    "preferredquality": abr,
                },
                {"key": "FFmpegMetadata"},   # embed title/artist tags
            ],
        }
        ext = "mp3"

    else:  # mp4
        fmt = VIDEO_FORMAT_MAP.get(quality, "bestvideo+bestaudio/best")
        ydl_opts = {
            **_base_ydl_opts(),
            "format":              fmt,
            "outtmpl":             out_tmpl,
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key":             "FFmpegVideoConvertor",
                    "preferedformat":  "mp4",
                },
                {"key": "FFmpegMetadata"},
            ],
        }
        ext = "mp4"

    # ── Run download in thread with timeout ──────────────────────────────
    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info = await asyncio.wait_for(
            asyncio.to_thread(_run),
            timeout=settings.DOWNLOAD_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        _cleanup_job(job_id)
        raise ValueError("Download timed out. The video may be too large or the server is slow.")
    except yt_dlp.utils.DownloadError as exc:
        _cleanup_job(job_id)
        raise ValueError(f"Download failed: {exc}") from exc
    except Exception as exc:
        _cleanup_job(job_id)
        raise RuntimeError(f"Unexpected error during download: {exc}") from exc

    # ── Locate output file ───────────────────────────────────────────────
    expected = TMP_DIR / f"{job_id}.{ext}"
    if expected.exists():
        final_path = str(expected)
    else:
        candidates = sorted(TMP_DIR.glob(f"{job_id}.*"))
        if not candidates:
            raise RuntimeError("Output file was not found after download completed.")
        final_path = str(candidates[0])

    title    = info.get("title") or "lumio_download"
    filename = safe_filename(title, ext)

    size_kb = os.path.getsize(final_path) // 1024
    logger.info(f"Download complete | job={job_id} | {filename} | {size_kb} KB")

    media_type = "audio/mpeg" if ext == "mp3" else "video/mp4"
    return DownloadResult(file_path=final_path, filename=filename, media_type=media_type)


def _cleanup_job(job_id: str):
    """Delete all temp files for a job (used on error paths)."""
    for f in TMP_DIR.glob(f"{job_id}.*"):
        try:
            f.unlink()
        except OSError:
            pass
