"""ingestion package — worker_fast public API (soup mode only, no crawl4ai)."""
from app.data_processing.ingestion.utils import normalize_url, resolve_crawl_mode
from app.data_processing.ingestion.file_ingester import (
    async_process_local_file,
    async_process_file_url,
)

__all__ = [
    "normalize_url",
    "resolve_crawl_mode",
    "async_process_local_file",
    "async_process_file_url",
]
