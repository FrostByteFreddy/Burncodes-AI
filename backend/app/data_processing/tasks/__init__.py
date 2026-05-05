"""
data_processing/tasks/__init__.py
Re-exports all Celery tasks so external imports (celery_worker.py, sources.py)
don't need to change their import paths.
"""
import asyncio
from uuid import UUID

from celery import shared_task
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.data_processing.tasks.crawl_tasks import crawl_links_task, process_single_url_task  # noqa: F401
from app.data_processing.tasks.maintenance_tasks import job_scheduler_task, zombie_reaper_task  # noqa: F401
from app.data_processing.ingestion.file_ingester import async_process_local_file
from app.data_processing.ingestion.url_ingester import process_urls_concurrently
from app.data_processing.processor import process_documents


@shared_task(queue="fast")
def process_local_file(file_path: str, source_filename: str, source_id: int, tenant_id: UUID):
    """Celery task to process a file stored on the local filesystem."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    docs = asyncio.run(async_process_local_file(file_path, source_filename, source_id, tenant_id))
    process_documents(docs, tenant_id, embeddings)


@shared_task(queue="fast")
def process_urls(urls: list[tuple[str, int]], tenant_id: UUID):
    """Celery task to process a batch of URLs concurrently."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    docs = asyncio.run(process_urls_concurrently(urls, tenant_id))
    process_documents(docs, tenant_id, embeddings)


__all__ = [
    "crawl_links_task",
    "process_single_url_task",
    "job_scheduler_task",
    "zombie_reaper_task",
    "process_local_file",
    "process_urls",
]

