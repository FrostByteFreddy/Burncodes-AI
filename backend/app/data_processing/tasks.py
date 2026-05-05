"""
data_processing/tasks.py — SHIM
This file exists solely for backward compatibility with any direct imports
such as `from app.data_processing.tasks import ...`.

All implementation has been moved to:
  - app/data_processing/chunking/    — LLM, fast, document chunkers
  - app/data_processing/ingestion/   — soup, Playwright, file ingesters
  - app/data_processing/tasks/       — Celery tasks (crawl + maintenance)
"""

# Celery tasks — re-exported for celery_worker.py autodiscovery
from app.data_processing.tasks.crawl_tasks import crawl_links_task, process_single_url_task  # noqa: F401
from app.data_processing.tasks.maintenance_tasks import job_scheduler_task, zombie_reaper_task  # noqa: F401

# Pure functions — re-exported for any callers that still import from this module
from app.data_processing.chunking.llm_chunker import (  # noqa: F401
    async_clean_and_chunk_markdown_with_llm,
    async_clean_pdf_text_with_llm,
)
from app.data_processing.chunking.fast_chunker import (  # noqa: F401
    async_create_document_chunks_fast,
    async_create_document_chunks_for_structured_data,
)
from app.data_processing.chunking.document_chunker import (  # noqa: F401
    async_create_document_chunks_with_metadata,
    async_create_document_chunks_for_pdf,
    get_document_chunks as _get_document_chunks,
    get_document_chunks_from_content as _get_document_chunks_from_content,
)
from app.data_processing.ingestion.utils import normalize_url, resolve_crawl_mode as _resolve_crawl_mode  # noqa: F401
from app.data_processing.ingestion.url_ingester import (  # noqa: F401
    async_fetch_and_chunk_soup,
    async_crawl_urls_for_content,
    process_urls_concurrently,
)
from app.data_processing.ingestion.file_ingester import (  # noqa: F401
    async_process_local_file,
    async_process_file_url,
)

# process_urls Celery task — kept here as it is a @shared_task
import asyncio
from uuid import UUID
from celery import shared_task
from langchain_google_genai import GoogleGenerativeAIEmbeddings
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
