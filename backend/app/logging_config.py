import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LOG_DIR = os.getenv("LOG_DIR", "/app/data/logs")
os.makedirs(LOG_DIR, exist_ok=True)

APP_LOG   = os.path.join(LOG_DIR, "app.log")
ERROR_LOG = os.path.join(LOG_DIR, "error.log")

# ---------------------------------------------------------------------------
# Shared formatter
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s %(pathname)s:%(lineno)d — %(message)s"
DATEFMT    = "%Y-%m-%dT%H:%M:%S"

formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATEFMT)


def _rotating_file_handler(path: str, level: int) -> TimedRotatingFileHandler:
    """
    Creates a TimedRotatingFileHandler that rolls over every 15 minutes.
    Keeps 7 days worth of rotated files (7 * 24 * 4 = 672 backups).
    """
    handler = TimedRotatingFileHandler(
        filename=path,
        when="M",           # minute-based rotation
        interval=15,        # roll every 15 minutes
        backupCount=672,    # 7 days × 24 h × 4 rotations/h
        encoding="utf-8",
        delay=True,         # don't create the file until first write
        utc=True,
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def _stdout_handler(level: int) -> logging.StreamHandler:
    """Sends all records at or above `level` to stdout (visible via docker logs)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def setup_logging() -> logging.Logger:
    """
    Configures and returns the application-wide logger.

    Handlers:
     - stdout      : INFO+  (always visible via `docker logs`)
     - app.log     : INFO+  rotated every 15 min, kept for 7 days
     - error.log   : ERROR+ rotated every 15 min, kept for 7 days
    """
    logger = logging.getLogger("burncodes_ai")
    logger.setLevel(logging.DEBUG)

    # Guard against duplicate handlers on hot-reload
    if logger.handlers:
        return logger

    logger.addHandler(_stdout_handler(logging.INFO))
    logger.addHandler(_rotating_file_handler(APP_LOG,   logging.INFO))
    logger.addHandler(_rotating_file_handler(ERROR_LOG, logging.ERROR))

    # Don't propagate to the root logger — keeps Flask's own output clean
    logger.propagate = False

    logger.info("Logging initialised — app=%s  error=%s", APP_LOG, ERROR_LOG)
    return logger


# Module-level singleton — imported everywhere as `from app.logging_config import error_logger`
error_logger = setup_logging()
