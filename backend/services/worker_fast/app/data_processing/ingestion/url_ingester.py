"""
ingestion/url_ingester.py
URL crawling and chunking pipeline — soup mode and Playwright/Crawl4AI mode.
"""
import os
import asyncio
from uuid import UUID
from urllib.parse import urlparse

from langchain_core.documents import Document

from app.database.supabase_client import supabase
from app.data_processing.processor import SUPPORTED_FILE_EXTENSIONS
from app.data_processing.crawler import get_crawler
from app.data_processing.config import CRAWLER_RUN_CONFIG
from app.data_processing.soup_extractor import fetch_html, extract_content
from app.data_processing.chunking.fast_chunker import async_create_document_chunks_fast
from app.data_processing.chunking.document_chunker import get_document_chunks
from app.data_processing.ingestion.utils import resolve_crawl_mode
from app.logging_config import error_logger


async def async_fetch_and_chunk_soup(url: str, source_id: int, tenant_id: UUID) -> list[Document]:
    """
    Soup pipeline: httpx fetch → trafilatura/BS4 extraction → fast chunker.
    No Playwright, no LLM.
    """
    loop = asyncio.get_running_loop()
    try:
        html, status_code = await loop.run_in_executor(None, lambda: fetch_html(url))
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status_code": status_code}).eq("id", source_id).execute(),
        )

        if not html or status_code >= 400:
            error_logger.warning("soup: empty/error response for %s (status=%s)", url, status_code)
            await loop.run_in_executor(
                None,
                lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
            )
            return []

        content = await loop.run_in_executor(None, lambda: extract_content(html, url))
        if not content:
            error_logger.warning("soup: no content extracted from %s", url)
            await loop.run_in_executor(
                None,
                lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
            )
            return []

        error_logger.info("soup: fetched %s (status=%s) — handing off to fast chunker", url, status_code)
        return await async_create_document_chunks_fast(content, url, source_id, tenant_id)

    except Exception as e:
        error_logger.error("soup: error processing %s: %s", url, e, exc_info=True)
        await loop.run_in_executor(
            None,
            lambda: supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute(),
        )
        return []


async def async_crawl_urls_for_content(
    urls_to_process: list[tuple[str, int]], tenant_id: UUID
) -> list[Document]:
    """Crawls URLs concurrently using Crawl4AI (Playwright) and processes their content."""
    all_docs = []
    semaphore = asyncio.Semaphore(30)
    crawler = get_crawler()
    await crawler.start()

    try:
        async def process_single_result(result, source_id, _tenant_id):
            async with semaphore:
                status_code = getattr(result, "status_code", None)
                if result.success and result.markdown:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: supabase.table("tenant_sources").update({"status_code": status_code}).eq("id", source_id).execute(),
                    )
                    ext = os.path.splitext(urlparse(result.url).path)[1].lower() or ".html"
                    return await get_document_chunks(result.markdown, result.url, source_id, ext, _tenant_id)
                else:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: supabase.table("tenant_sources").update({
                            "status": "ERROR",
                            "status_code": status_code if status_code else 500,
                        }).eq("id", source_id).execute(),
                    )
            return []

        url_to_source_id = {url: source_id for url, source_id in urls_to_process}
        results = await crawler.arun_many(urls=list(url_to_source_id.keys()), config=CRAWLER_RUN_CONFIG)
        tasks = [process_single_result(result, url_to_source_id[result.url], tenant_id) for result in results]
        processed_chunks_list = await asyncio.gather(*tasks)
        for doc_list in processed_chunks_list:
            all_docs.extend(doc_list)
        return all_docs
    finally:
        await crawler.close()


async def process_urls_concurrently(urls: list[tuple[str, int]], tenant_id: UUID) -> list[Document]:
    """Routes a batch of URLs to the correct ingestion pipeline and processes them concurrently."""
    from app.data_processing.ingestion.file_ingester import async_process_file_url

    urls_to_crawl = []
    file_urls_to_process = []
    crawl_mode = await resolve_crawl_mode(tenant_id)

    for url, source_id in urls:
        ext = os.path.splitext(urlparse(url).path)[1].lower()
        if ext in SUPPORTED_FILE_EXTENSIONS:
            file_urls_to_process.append((url, source_id))
        else:
            urls_to_crawl.append((url, source_id))

    tasks = []
    if urls_to_crawl:
        if crawl_mode == "soup":
            error_logger.info("process_urls: crawl_mode=soup — routing %d URL(s) to soup pipeline", len(urls_to_crawl))
            for url, source_id in urls_to_crawl:
                tasks.append(async_fetch_and_chunk_soup(url, source_id, tenant_id))
        else:
            tasks.append(async_crawl_urls_for_content(urls_to_crawl, tenant_id))

    for file_url, source_id in file_urls_to_process:
        tasks.append(async_process_file_url(file_url, tenant_id, source_id))

    results = await asyncio.gather(*tasks)
    all_docs = []
    for result_list in results:
        if result_list:
            all_docs.extend(result_list)
    return all_docs
