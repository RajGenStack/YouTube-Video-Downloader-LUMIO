"""
app/routes.py
All HTTP routes for the Lumio API.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import yt_dlp

from app.cleanup import delete_file
from app.config import get_settings
from app.downloader import download_media, fetch_video_info
from app.logger import logger
from app.schemas import (
    DownloadRequest,
    ErrorResponse,
    FetchInfoRequest,
    HealthResponse,
    VideoInfoResponse,
    VALID_MP3_QUALITIES,
    VALID_MP4_QUALITIES,
)

settings = get_settings()
router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ── Health ───────────────────────────────────────────────────────────────────
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health():
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        yt_dlp_version=yt_dlp.version.__version__,
    )


# ── Fetch info ───────────────────────────────────────────────────────────────
@router.post(
    "/api/fetch-info",
    response_model=VideoInfoResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Invalid URL or private video"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Fetch YouTube video metadata",
    tags=["Downloader"],
)
@limiter.limit(settings.RATE_LIMIT_FETCH)
async def fetch_info(request: Request, body: FetchInfoRequest):
    logger.info(f"fetch-info | ip={get_remote_address(request)} | url={body.url[:80]}")
    try:
        info = await fetch_video_info(body.url)
        return info
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Unexpected error in fetch-info: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching video info.")


# ── Download ─────────────────────────────────────────────────────────────────
@router.post(
    "/api/download",
    responses={
        200: {"description": "Binary file stream (MP3 or MP4)"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Download failed"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Download YouTube video or audio",
    tags=["Downloader"],
)
@limiter.limit(settings.RATE_LIMIT_DOWNLOAD)
async def download(
    request: Request,
    body: DownloadRequest,
    background_tasks: BackgroundTasks,
):
    # Extra cross-field validation
    if body.mode == "mp3" and body.quality not in VALID_MP3_QUALITIES:
        raise HTTPException(
            status_code=400,
            detail=f"For MP3, quality must be one of: {sorted(VALID_MP3_QUALITIES)}",
        )
    if body.mode == "mp4" and body.quality not in VALID_MP4_QUALITIES:
        raise HTTPException(
            status_code=400,
            detail=f"For MP4, quality must be one of: {sorted(VALID_MP4_QUALITIES)}",
        )

    logger.info(
        f"download | ip={get_remote_address(request)} "
        f"| mode={body.mode} | quality={body.quality} "
        f"| url={body.url[:80]}"
    )

    try:
        result = await download_media(body.url, body.mode, body.quality)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        logger.error(f"RuntimeError during download: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Unexpected error during download: {exc}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during download.")

    # Schedule temp file deletion after response is sent
    background_tasks.add_task(delete_file, result.file_path)

    import urllib.parse
    encoded_filename = urllib.parse.quote(result.filename)
    return FileResponse(
        path=result.file_path,
        filename=result.filename,
        media_type=result.media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
            "X-Lumio-Quality": body.quality,
            "X-Lumio-Mode": body.mode,
        },
    )
