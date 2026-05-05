"""ingestion package — public API."""
from app.data_processing.ingestion.utils import normalize_url, resolve_crawl_mode
from app.data_processing.ingestion.url_ingester import (
    async_fetch_and_chunk_soup,
    async_crawl_urls_for_content,
    process_urls_concurrently,
)
from app.data_processing.ingestion.file_ingester import (
    async_process_local_file,
    async_process_file_url,
)

__all__ = [
    "normalize_url",
    "resolve_crawl_mode",
    "async_fetch_and_chunk_soup",
    "async_crawl_urls_for_content",
    "process_urls_concurrently",
    "async_process_local_file",
    "async_process_file_url",
]
