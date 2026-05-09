"""
chunking/document_chunker.py
High-level chunking dispatcher and LLM-powered document chunkers (markdown + PDF).
"""
import os
import re
import asyncio
from datetime import datetime, timezone
from uuid import UUID

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.database.supabase_client import supabase
from app.billing.services import BillingService
from app.logging_config import error_logger
from app.data_processing.chunking.llm_chunker import (
    async_clean_and_chunk_markdown_with_llm,
    async_clean_pdf_text_with_llm,
    INDEXING_GEMINI_MODEL,
)
from app.data_processing.chunking.fast_chunker import (
    async_create_document_chunks_fast,
    async_create_document_chunks_for_structured_data,
)


async def async_create_document_chunks_with_metadata(
    content: str, source: str, source_id: int, tenant_id: UUID
) -> list[Document]:
    """Cleans, chunks, and creates Document objects with LLM + metadata."""
    loop = asyncio.get_running_loop()
    try:
        tenant_response = await loop.run_in_executor(
            None,
            lambda: supabase.table("tenants").select("doc_language").eq("id", str(tenant_id)).single().execute(),
        )
        doc_language = tenant_response.data.get("doc_language", "en") if tenant_response.data else "en"

        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "PROCESSING"}).eq("id", source_id).execute(),
        )

        cleaned_and_chunked_content, input_tokens, output_tokens = await async_clean_and_chunk_markdown_with_llm(
            content, doc_language, source_id
        )

        if not cleaned_and_chunked_content.strip():
            error_logger.warning(
                "source_id=%s produced no chunks (empty content) — marking COMPLETED with 0 chunks.", source_id
            )
            await loop.run_in_executor(
                None,
                lambda: supabase.table("tenant_sources").update({"status": "COMPLETED", "chunk_count": 0}).eq("id", source_id).execute(),
            )
            return []

        user_response = await loop.run_in_executor(
            None,
            lambda: supabase.table("tenants").select("user_id").eq("id", str(tenant_id)).single().execute(),
        )
        if user_response.data:
            user_id = user_response.data["user_id"]
            cost = BillingService.deduct_cost(user_id, INDEXING_GEMINI_MODEL, input_tokens, output_tokens)
            await loop.run_in_executor(
                None,
                lambda: supabase.table("tenant_sources").update({
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_chf": cost,
                }).eq("id", source_id).execute(),
            )

        chunks = [c.strip() for c in cleaned_and_chunked_content.split("---CHUNK_SEPARATOR---") if c.strip()]

        try:
            os.makedirs("crawled_markdown", exist_ok=True)
            safe_filename = re.sub(r"https://?|www\\.|\\/|\\?|\\=|\\&", "_", source) + ".md"
            filepath = os.path.join("crawled_markdown", safe_filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# SOURCE: {source}\n\n{cleaned_and_chunked_content}")
        except Exception as e:
            error_logger.warning("Could not save cleaned markdown file for %s: %s", source, e)

        timestamp = datetime.now(timezone.utc).isoformat()
        return [
            Document(
                page_content=chunk,
                metadata={"source": source, "source_id": source_id, "chunk": i, "last_updated": timestamp},
            )
            for i, chunk in enumerate(chunks)
        ]

    except Exception as e:
        error_logger.error("Error creating document chunks for source %s: %s", source_id, e, exc_info=True)
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
        )
        return []


async def async_create_document_chunks_for_pdf(
    content: str, source: str, source_id: int, tenant_id: UUID
) -> list[Document]:
    """Cleans and chunks PDF content using LLM + RecursiveCharacterTextSplitter."""
    loop = asyncio.get_running_loop()
    try:
        tenant_response = await loop.run_in_executor(
            None,
            lambda: supabase.table("tenants").select("doc_language").eq("id", str(tenant_id)).single().execute(),
        )
        doc_language = tenant_response.data.get("doc_language", "en") if tenant_response.data else "en"

        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "PROCESSING"}).eq("id", source_id).execute(),
        )

        sanitized_content = content.replace("\x00", "")
        large_splitter = RecursiveCharacterTextSplitter(
            chunk_size=5000, chunk_overlap=200, length_function=len, is_separator_regex=False
        )
        large_chunks = large_splitter.split_text(sanitized_content)

        cleaned_chunks, total_input_tokens, total_output_tokens = [], 0, 0
        for i, chunk in enumerate(large_chunks):
            error_logger.debug("Processing large PDF chunk %d/%d for source_id=%s", i + 1, len(large_chunks), source_id)
            cleaned_chunk, inp, out = await async_clean_pdf_text_with_llm(chunk, doc_language)
            cleaned_chunks.append(cleaned_chunk)
            total_input_tokens += inp
            total_output_tokens += out

        user_response = await loop.run_in_executor(
            None,
            lambda: supabase.table("tenants").select("user_id").eq("id", str(tenant_id)).single().execute(),
        )
        if user_response.data:
            user_id = user_response.data["user_id"]
            cost = BillingService.deduct_cost(user_id, INDEXING_GEMINI_MODEL, total_input_tokens, total_output_tokens)
            await loop.run_in_executor(
                None,
                lambda: supabase.table("tenant_sources").update({
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "cost_chf": cost,
                }).eq("id", source_id).execute(),
            )

        full_cleaned_content = "\n\n---CHUNK_SEPARATOR---\n\n".join(cleaned_chunks)

        filename_stem = os.path.splitext(os.path.basename(source))[0]
        readme_dir = os.path.join(os.environ.get("UPLOADS_DIR", "/app/data/uploads"), str(tenant_id), "readme_output")
        os.makedirs(readme_dir, exist_ok=True)
        with open(os.path.join(readme_dir, f"{filename_stem}.md"), "w", encoding="utf-8") as f:
            f.write(full_cleaned_content)

        chunks = [c.strip() for c in full_cleaned_content.split("---CHUNK_SEPARATOR---") if c.strip()]
        timestamp = datetime.now(timezone.utc).isoformat()
        documents = [
            Document(
                page_content=chunk,
                metadata={"source": source, "source_id": source_id, "chunk": i, "last_updated": timestamp},
            )
            for i, chunk in enumerate(chunks)
        ]
        error_logger.info("Created %d document chunks for PDF %s (source_id: %s)", len(documents), source, source_id)
        return documents

    except Exception as e:
        error_logger.error("Error creating document chunks for PDF source %s: %s", source_id, e, exc_info=True)
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
        )
        return []


async def get_document_chunks(
    content: str, source: str, source_id: int, ext: str, tenant_id: UUID
) -> list[Document]:
    """
    Unified chunking dispatcher for already-fetched content.

    crawl_mode routing:
      'soup'           → fast splitter
      'playwright'     → fast splitter on Crawl4AI markdown
      'playwright_llm' → LLM cleaning + semantic chunking (default)
    Structured data (CSV, ICS) always bypasses LLM regardless of mode.
    """
    from app.data_processing.ingestion.utils import resolve_crawl_mode

    structured_extensions = [".csv", ".ics"]
    if ext in structured_extensions:
        return await async_create_document_chunks_for_structured_data(content, source, source_id)

    crawl_mode = await resolve_crawl_mode(tenant_id)

    if crawl_mode in ("soup", "playwright"):
        error_logger.info("crawl_mode=%s for source_id=%s — using fast splitter", crawl_mode, source_id)
        return await async_create_document_chunks_fast(content, source, source_id, tenant_id)

    if ext == ".pdf":
        return await async_create_document_chunks_for_pdf(content, source, source_id, tenant_id)
    return await async_create_document_chunks_with_metadata(content, source, source_id, tenant_id)


async def get_document_chunks_from_content(
    content: str, source: str, source_id: int, ext: str, tenant_id: UUID
) -> list[Document]:
    """File-extension-based chunking dispatcher (for local files and file URLs)."""
    structured_extensions = [".csv", ".ics"]
    if ext in structured_extensions:
        return await async_create_document_chunks_for_structured_data(content, source, source_id)
    elif ext == ".pdf":
        return await async_create_document_chunks_for_pdf(content, source, source_id, tenant_id)
    else:
        return await async_create_document_chunks_with_metadata(content, source, source_id, tenant_id)
