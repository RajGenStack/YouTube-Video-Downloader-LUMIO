"""
app/logger.py
Structured JSON logging for production, human-readable for development.
"""
import logging
import sys
from app.config import get_settings

settings = get_settings()


def setup_logging() -> logging.Logger:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if settings.ENVIRONMENT == "production":
        # JSON-style for log aggregators (Datadog, Logtail, etc.)
        fmt = '{"time":"%(asctime)s","level":"%(levelname)s","module":"%(module)s","msg":"%(message)s"}'
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s"

    logging.basicConfig(
        level=log_level,
        format=fmt,
        handlers=handlers,
    )

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logging.getLogger("lumio")


logger = setup_logging()
