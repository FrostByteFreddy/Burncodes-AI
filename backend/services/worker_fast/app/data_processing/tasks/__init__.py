"""
worker_fast/app/data_processing/tasks/__init__.py

Fast-queue Celery tasks. No Playwright — soup/trafilatura only.
File Search replaces the old ChromaDB/LangChain pipeline.
"""
from pathlib import Path
from urllib.parse import urlparse

from celery import shared_task

from app.data_processing.ingestion.file_ingester import (
    process_local_file as _index_local_file,
    process_file_url as _index_file_url,
    process_webpage as _index_webpage,
)
from app.gemini_store.service import INDEXABLE_FILE_EXTENSIONS
from app.data_processing.tasks.maintenance_tasks import job_scheduler_task, zombie_reaper_task  # noqa: F401
from app.logging_config import error_logger


@shared_task(name="app.data_processing.tasks.process_local_file", queue="fast")
def process_local_file(file_path: str, source_filename: str, source_id: int, tenant_id: str):
    """Index a file already saved on disk into the tenant's File Search Store."""
    _index_local_file(file_path, source_filename, source_id, str(tenant_id))


@shared_task(name="app.data_processing.tasks.process_file_url", queue="fast")
def process_file_url(url: str, source_id: int, tenant_id: str):
    """Download a remote file URL and index it in the tenant's File Search Store."""
    _index_file_url(url, source_id, str(tenant_id))


@shared_task(name="app.data_processing.tasks.process_urls", queue="fast")
def process_urls(urls: list, tenant_id: str):
    """
    Routes a list of manually-added URLs (url, source_id) pairs.

    - File URLs (PDF, DOCX, images, etc.) → process_file_url task
    - Web pages → trafilatura extraction → File Search upload (inline, soup mode)
    """
    for url, source_id in urls:
        ext = Path(urlparse(url).path).suffix.lower()
        try:
            if ext in INDEXABLE_FILE_EXTENSIONS:
                error_logger.info("process_urls: routing file URL %s to process_file_url", url)
                process_file_url.apply_async(
                    args=[url, source_id, str(tenant_id)], queue="fast"
                )
            else:
                error_logger.info("process_urls: indexing web page %s via trafilatura", url)
                _index_webpage(url, source_id, str(tenant_id))
        except Exception as e:
            error_logger.error("process_urls: failed for %s (source %s): %s", url, source_id, e, exc_info=True)


__all__ = [
    "process_local_file",
    "process_file_url",
    "process_urls",
    "job_scheduler_task",
    "zombie_reaper_task",
]
