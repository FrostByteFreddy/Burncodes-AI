"""
services/worker_fast/app/data_processing/tasks/__init__.py
Exports fast-queue tasks only — no crawl4ai imports.
"""
import asyncio
from uuid import UUID

from celery import shared_task
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.data_processing.ingestion.file_ingester import async_process_local_file
from app.data_processing.ingestion.url_ingester import process_urls_concurrently
from app.data_processing.processor import process_documents
from app.data_processing.tasks.maintenance_tasks import job_scheduler_task, zombie_reaper_task  # noqa: F401


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
    "process_local_file",
    "process_urls",
    "job_scheduler_task",
    "zombie_reaper_task",
]
