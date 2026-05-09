import io
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# ---------------------------------------------------------------------------
# Log directory
# ---------------------------------------------------------------------------
LOG_DIR = os.getenv("LOG_DIR", "/app/data/logs")
os.makedirs(LOG_DIR, exist_ok=True)

APP_LOG   = os.path.join(LOG_DIR, "app.log")
ERROR_LOG = os.path.join(LOG_DIR, "error.log")
DEBUG_LOG = os.path.join(LOG_DIR, "debug.log")

# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------
LOG_FORMAT = (
    "%(asctime)s [%(levelname)s] %(name)s "
    "%(pathname)s:%(lineno)d — %(message)s"
)
DATEFMT = "%Y-%m-%dT%H:%M:%S"

formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATEFMT)


# ---------------------------------------------------------------------------
# Handler factory
# ---------------------------------------------------------------------------
def _rotating(path: str, level: int) -> TimedRotatingFileHandler:
    """15-minute rolling file handler, 7 days retention."""
    h = TimedRotatingFileHandler(
        filename=path,
        when="M",
        interval=15,
        backupCount=672,   # 7 days × 24 h × 4 rotations/h
        encoding="utf-8",
        delay=True,
        utc=True,
    )
    h.setLevel(level)
    h.setFormatter(formatter)
    return h


def _stdout(level: int) -> logging.StreamHandler:
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(level)
    h.setFormatter(formatter)
    return h


# ---------------------------------------------------------------------------
# PrintToLogger — redirects sys.stdout so print() calls land in the log
# ---------------------------------------------------------------------------
class _PrintCapture(io.TextIOBase):
    """
    Replaces sys.stdout so that every print() call is forwarded to the
    application logger at INFO level.  The real stdout is kept alive so
    that the log StreamHandler can still write to it.
    """
    def __init__(self, logger: logging.Logger, real_stdout):
        self._logger = logger
        self._real  = real_stdout
        self._buf   = ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            stripped = line.rstrip()
            if stripped:
                self._logger.info("[print] %s", stripped)
        return len(text)

    def flush(self):
        # flush any partial line that has no trailing newline
        if self._buf.strip():
            self._logger.info("[print] %s", self._buf.strip())
            self._buf = ""

    # Delegate everything else so libraries that check sys.stdout attributes work
    def fileno(self):          return self._real.fileno()
    def isatty(self):          return False
    def readable(self):        return False
    def writable(self):        return True
    def seekable(self):        return False


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """
    Configure the application logger with three rotating file handlers
    plus a stdout mirror.  Also captures:
      - sys.stdout (print statements) → INFO
      - root logger (third-party libs) → WARNING
    """
    logger = logging.getLogger("burncodes_ai")

    if logger.handlers:
        return logger   # already initialised (hot-reload guard)

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Our own handlers
    logger.addHandler(_stdout(logging.INFO))
    logger.addHandler(_rotating(APP_LOG,   logging.INFO))
    logger.addHandler(_rotating(ERROR_LOG, logging.ERROR))
    logger.addHandler(_rotating(DEBUG_LOG, logging.DEBUG))

    # ── Third-party libraries (LangChain, ChromaDB, httpx, Celery …) ──────
    # Wire them to the root logger so their WARNING+ messages land in our files
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    if not root.handlers:
        root.addHandler(_rotating(APP_LOG,   logging.WARNING))
        root.addHandler(_rotating(DEBUG_LOG, logging.DEBUG))

    # ── Capture print() calls ─────────────────────────────────────────────
    real_stdout = sys.stdout
    sys.stdout  = _PrintCapture(logger, real_stdout)

    logger.info(
        "Logging initialised — app=%s  error=%s  debug=%s",
        APP_LOG, ERROR_LOG, DEBUG_LOG,
    )
    return logger


# Module-level singleton — imported everywhere as:
#   from app.logging_config import error_logger
error_logger = setup_logging()
