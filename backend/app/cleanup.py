"""
app/cleanup.py
Periodic background task that sweeps the temp directory and removes
any files older than CLEANUP_AFTER_SECONDS.
This is a safety net; per-request cleanup already runs via BackgroundTasks.
"""
import asyncio
import os
import time
from pathlib import Path

from app.config import get_settings
from app.logger import logger

settings = get_settings()
TMP_DIR = Path(settings.TMP_DIR)


async def cleanup_loop():
    """Run forever, sweeping stale files every 60 seconds."""
    while True:
        await asyncio.sleep(60)
        _sweep()


def _sweep():
    if not TMP_DIR.exists():
        return
    now = time.time()
    cutoff = settings.CLEANUP_AFTER_SECONDS
    removed = 0
    for f in TMP_DIR.iterdir():
        try:
            age = now - f.stat().st_mtime
            if age > cutoff:
                f.unlink()
                removed += 1
        except OSError:
            pass
    if removed:
        logger.info(f"Cleanup sweep: removed {removed} stale file(s) from {TMP_DIR}")


def delete_file(path: str):
    """Delete a single file — used as a FastAPI BackgroundTask."""
    try:
        os.remove(path)
        logger.debug(f"Deleted temp file: {path}")
    except FileNotFoundError:
        pass
    except OSError as e:
        logger.warning(f"Could not delete {path}: {e}")
