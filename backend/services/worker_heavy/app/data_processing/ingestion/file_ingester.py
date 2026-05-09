"""
ingestion/file_ingester.py
Local file and remote file-URL ingestion pipeline.
"""
import os
import asyncio
import tempfile
import httpx
from uuid import UUID
from urllib.parse import urlparse

from langchain_core.documents import Document

from app.database.supabase_client import supabase
from app.data_processing.processor import get_loader, SUPPORTED_FILE_EXTENSIONS
from app.data_processing.chunking.document_chunker import get_document_chunks, get_document_chunks_from_content
from app.logging_config import error_logger


async def async_process_local_file(
    file_path: str, source_filename: str, source_id: int, tenant_id: UUID
) -> list[Document]:
    """Reads a file from local storage and processes it into document chunks."""
    ext = os.path.splitext(source_filename)[1].lower()
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")

        loader = get_loader(file_path)
        if not loader:
            error_logger.warning("No loader found for extension %s, skipping file %s", ext, source_filename)
            return []

        docs_from_loader = loader.load()
        if not docs_from_loader:
            return []

        content = "\n\n".join([doc.page_content for doc in docs_from_loader])
        return await get_document_chunks(content, source_filename, source_id, ext, tenant_id)

    except Exception as e:
        error_logger.error("Error processing local file %s: %s", file_path, e, exc_info=True)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
        )
        return []


async def async_process_file_url(url: str, tenant_id: UUID, source_id: int) -> list[Document]:
    """Downloads a file from a URL and processes its content."""
    error_logger.info("Downloading and processing file: %s", url)
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if not ext:
        return []

    tmp_filepath = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()

        tenant_upload_path = os.path.join("uploads", str(tenant_id))
        os.makedirs(tenant_upload_path, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=tenant_upload_path) as tmp_file:
            tmp_file.write(response.content)
            tmp_filepath = tmp_file.name

        loader = get_loader(tmp_filepath)
        if not loader:
            error_logger.warning("No loader found for extension %s, skipping file URL %s", ext, url)
            os.remove(tmp_filepath)
            return []

        docs_from_loader = loader.load()
        os.remove(tmp_filepath)

        if not docs_from_loader:
            return []

        content = "\n\n".join([doc.page_content for doc in docs_from_loader])
        return await get_document_chunks_from_content(content, url, source_id, ext, tenant_id)

    except Exception as e:
        error_logger.error("Error processing file URL %s: %s", url, e, exc_info=True)
        if tmp_filepath and os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)
        return []
