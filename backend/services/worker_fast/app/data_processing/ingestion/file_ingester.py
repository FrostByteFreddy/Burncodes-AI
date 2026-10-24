"""
worker_fast/app/data_processing/ingestion/file_ingester.py

Uploads local files and remote file URLs to the tenant's Gemini File Search Store.
Replaces the old LangChain/ChromaDB pipeline entirely.
"""
from pathlib import Path
from urllib.parse import urlparse

from app.billing.services import BillingService
from app.database.supabase_client import supabase
from app.data_processing.soup_extractor import HEADERS, fetch_html
from app.security.url_guard import UnsafeURLError, safe_client
from app.gemini_store.service import GeminiStoreService, INDEXABLE_FILE_EXTENSIONS, UNSUPPORTED_EXTENSIONS
from app.logging_config import error_logger


def _require_balance(source_id: int, tenant_id: str) -> bool:
    """Marks the source as failed (402) and returns False if the owner has no balance."""
    if BillingService.tenant_has_balance(tenant_id):
        return True
    error_logger.warning("Skipping source %s: tenant %s has no balance", source_id, tenant_id)
    supabase.table("tenant_sources").update({
        "status": "ERROR", "status_code": 402,
    }).eq("id", source_id).execute()
    return False


def process_local_file(file_path: str, source_filename: str, source_id: int, tenant_id: str) -> None:
    """
    Uploads a file already on disk to the tenant's File Search Store.
    Called from the process_local_file Celery task.
    """
    ext = Path(source_filename).suffix.lower()

    if ext in UNSUPPORTED_EXTENSIONS:
        error_logger.warning("Unsupported file type %s for source %s", ext, source_id)
        supabase.table("tenant_sources").update({
            "status": "UNSUPPORTED",
        }).eq("id", source_id).execute()
        return

    if not _require_balance(source_id, tenant_id):
        return
    supabase.table("tenant_sources").update({"status": "PROCESSING"}).eq("id", source_id).execute()
    try:
        store_name = GeminiStoreService.get_or_create_store(tenant_id)
        doc_name = GeminiStoreService.upload_file(
            store_name=store_name,
            file_path=file_path,
            display_name=source_filename,
            metadata={"tenant_id": tenant_id, "source_id": str(source_id)},
        )
        supabase.table("tenant_sources").update({
            "gemini_document_name": doc_name,
            "status": "COMPLETED",
        }).eq("id", source_id).execute()
        error_logger.info("Indexed local file %s (source %s)", source_filename, source_id)
    except Exception as e:
        error_logger.error("Failed to index local file %s: %s", source_filename, e, exc_info=True)
        supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()


def process_file_url(url: str, source_id: int, tenant_id: str) -> None:
    """
    Downloads a file from a URL and uploads it to the tenant's File Search Store.
    Used for:
      - Manual file URL entries (e.g. user pastes a PDF link)
      - FILE_URL sources discovered automatically during a site crawl
    """
    filename = Path(urlparse(url).path).name or "document"
    ext = Path(filename).suffix.lower()

    if ext in UNSUPPORTED_EXTENSIONS:
        error_logger.warning("Unsupported file type %s at %s (source %s)", ext, url, source_id)
        supabase.table("tenant_sources").update({"status": "UNSUPPORTED"}).eq("id", source_id).execute()
        return

    if not _require_balance(source_id, tenant_id):
        return
    supabase.table("tenant_sources").update({"status": "PROCESSING"}).eq("id", source_id).execute()
    try:
        error_logger.info("Downloading file URL %s", url)
        with safe_client(follow_redirects=True, timeout=60.0, headers={"User-Agent": HEADERS["User-Agent"]}) as client:
            response = client.get(url)
        response.raise_for_status()

        store_name = GeminiStoreService.get_or_create_store(tenant_id)
        doc_name = GeminiStoreService.upload_bytes(
            store_name=store_name,
            content=response.content,
            filename=filename,
            display_name=filename,
            metadata={"tenant_id": tenant_id, "source_id": str(source_id), "source_url": url},
        )
        supabase.table("tenant_sources").update({
            "gemini_document_name": doc_name,
            "status": "COMPLETED",
        }).eq("id", source_id).execute()
        error_logger.info("Indexed file URL %s (source %s)", url, source_id)
    except UnsafeURLError as e:
        error_logger.warning("Refusing to fetch file URL %s: %s", url, e)
        supabase.table("tenant_sources").update({"status": "ERROR", "status_code": 403}).eq("id", source_id).execute()
    except Exception as e:
        error_logger.error("Failed to index file URL %s: %s", url, e, exc_info=True)
        supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()


def process_webpage(url: str, source_id: int, tenant_id: str) -> None:
    """
    Fetches a web page with trafilatura (soup mode — no Playwright in worker_fast)
    and uploads the extracted text to the tenant's File Search Store.

    Used for manually-added web page URLs (not the recursive Playwright crawl).
    """
    import trafilatura

    if not _require_balance(source_id, tenant_id):
        return
    supabase.table("tenant_sources").update({"status": "PROCESSING"}).eq("id", source_id).execute()
    try:
        downloaded, status_code = fetch_html(url)
        if not downloaded:
            error_logger.warning("trafilatura: empty response for %s", url)
            supabase.table("tenant_sources").update({
                "status": "ERROR", "status_code": status_code,
            }).eq("id", source_id).execute()
            return

        text = trafilatura.extract(
            downloaded, url=url,
            include_links=False, include_images=False,
            output_format="markdown",
        )
        if not text:
            error_logger.warning("trafilatura: no content extracted from %s", url)
            supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()
            return

        store_name = GeminiStoreService.get_or_create_store(tenant_id)
        doc_name = GeminiStoreService.upload_text(
            store_name=store_name,
            text=text,
            display_name=url,
            metadata={"tenant_id": tenant_id, "source_id": str(source_id), "source_url": url},
        )
        supabase.table("tenant_sources").update({
            "gemini_document_name": doc_name,
            "status": "COMPLETED",
        }).eq("id", source_id).execute()
        error_logger.info("Indexed web page %s (source %s)", url, source_id)
    except Exception as e:
        error_logger.error("Failed to index web page %s: %s", url, e, exc_info=True)
        supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()
