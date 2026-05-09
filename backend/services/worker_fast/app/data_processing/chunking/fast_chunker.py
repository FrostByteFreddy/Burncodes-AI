"""
chunking/fast_chunker.py
Token-free, no-LLM indexing path shared by 'soup' and 'playwright' modes.
"""
import asyncio
from datetime import datetime, timezone
from uuid import UUID

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.database.supabase_client import supabase
from app.data_processing.soup_extractor import filter_chunks
from app.logging_config import error_logger


async def async_create_document_chunks_fast(
    content: str, source: str, source_id: int, tenant_id: UUID
) -> list[Document]:
    """
    Token-free indexing path — shared by 'soup' and 'playwright' modes.
    Raw content is sanitized, split with RecursiveCharacterTextSplitter,
    and passed through a heuristic quality filter. No LLM, zero token cost.
    """
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "PROCESSING"}).eq("id", source_id).execute(),
        )

        sanitized = content.replace("\x00", "")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        raw_chunks = splitter.split_text(sanitized)
        clean_chunks = await loop.run_in_executor(None, lambda: filter_chunks(raw_chunks))

        timestamp = datetime.now(timezone.utc).isoformat()
        documents = [
            Document(
                page_content=chunk,
                metadata={"source": source, "source_id": source_id, "chunk": i, "last_updated": timestamp},
            )
            for i, chunk in enumerate(clean_chunks)
            if chunk.strip()
        ]

        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({
                "input_tokens": 0, "output_tokens": 0, "cost_chf": 0.0,
            }).eq("id", source_id).execute(),
        )

        error_logger.info("fast-index: %d chunks for source_id=%s (no LLM, no cost)", len(documents), source_id)
        return documents

    except Exception as e:
        error_logger.error("fast-index: error for source_id=%s: %s", source_id, e, exc_info=True)
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
        )
        return []


async def async_create_document_chunks_for_structured_data(
    content: str, source: str, source_id: int
) -> list[Document]:
    """Chunks structured data (CSV, ICS) without LLM cleaning — single document per file."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "PROCESSING"}).eq("id", source_id).execute(),
        )
        timestamp = datetime.now(timezone.utc).isoformat()
        doc = Document(
            page_content=content,
            metadata={"source": source, "source_id": source_id, "chunk": 0, "last_updated": timestamp},
        )
        error_logger.info("Created 1 document for structured file %s (source_id: %s)", source, source_id)
        return [doc]
    except Exception as e:
        error_logger.error("Error creating document chunks for structured source %s: %s", source_id, e, exc_info=True)
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
        )
        return []
