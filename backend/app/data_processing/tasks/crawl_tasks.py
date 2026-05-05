"""
tasks/crawl_tasks.py
Celery tasks for distributed web crawling.
"""
import os
import asyncio
import random
from uuid import UUID

import httpx
from celery import shared_task
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LinkPreviewConfig

from app.database.supabase_client import supabase
from app.data_processing.processor import get_vectorstore, process_documents
from app.data_processing.crawler import get_crawler, browser_config
from app.data_processing.soup_extractor import fetch_html, extract_internal_links
from app.data_processing.chunking.document_chunker import get_document_chunks
from app.data_processing.ingestion.url_ingester import async_fetch_and_chunk_soup
from app.data_processing.ingestion.utils import normalize_url
from app.models.database import CrawlingStatus
from app.logging_config import error_logger

from langchain_google_genai import GoogleGenerativeAIEmbeddings


@shared_task(bind=True, queue="fast")
def crawl_links_task(
    self,
    tenant_id: UUID,
    start_url: str,
    single_page_only: bool = False,
    excluded_urls: list[str] = None,
    max_depth: int = 3,
):
    """
    Orchestrator Celery task — creates a CrawlingJob and fires the first CrawlingTask.
    """
    try:
        start_url = normalize_url(start_url)
        effective_max_depth = 1 if single_page_only else max_depth

        job_data = {
            "tenant_id": str(tenant_id),
            "start_url": start_url,
            "max_depth": effective_max_depth,
            "status": CrawlingStatus.IN_PROGRESS.value,
            "excluded_urls": excluded_urls or [],
        }
        job_response = supabase.table("crawling_jobs").insert(job_data).execute()
        job = job_response.data[0]
        job_id = job["id"]

        self.update_state(state="PROGRESS", meta={"job_id": job_id, "status": "Job created"})

        task_data = {
            "job_id": job_id,
            "url": start_url,
            "depth": 1,
            "status": CrawlingStatus.PENDING.value,
        }
        task_response = supabase.table("crawling_tasks").insert(task_data).execute()
        task_id = task_response.data[0]["id"]

        process_single_url_task.delay(task_id=task_id, tenant_id=tenant_id)
        return {"status": "Crawl initiated", "job_id": job_id}

    except Exception as e:
        error_message = f"Failed to initiate crawl: {e}"
        error_logger.error(error_message)
        if "job_id" in locals():
            supabase.table("crawling_jobs").update({"status": CrawlingStatus.FAILED.value}).eq("id", job_id).execute()
        self.update_state(state="FAILURE", meta={"status": error_message})
        raise e


@shared_task(bind=True, queue="heavy", time_limit=600)
def process_single_url_task(self, task_id: int, tenant_id: UUID, parent_url: str = None):
    """
    Worker Celery task — crawls a single URL, indexes content, and discovers new links.
    """
    task_details = {}
    try:
        task_response = supabase.table("crawling_tasks").select("*, crawling_jobs(*)").eq("id", task_id).execute()
        if not task_response.data:
            error_logger.debug("Task %s not found in DB (job deleted while queued) — discarding.", task_id)
            return
        task_details = task_response.data[0]

        job = task_details["crawling_jobs"]
        job_id = job["id"]
        url = task_details["url"]
        depth = task_details["depth"]
        max_depth = job["max_depth"]
        excluded_urls = job.get("excluded_urls", [])

        # 1. Normalize
        normalized_url = normalize_url(url)
        normalized_excluded_list = [normalize_url(str(ex).strip()) for ex in excluded_urls]

        # 2. Exclusion check
        is_excluded = False
        for excluded in normalized_excluded_list:
            if not excluded:
                continue
            stripped_ex = excluded.replace("https://", "").replace("http://", "").strip("/")
            stripped_url = normalized_url.replace("https://", "").replace("http://", "").strip("/")
            if stripped_ex and (stripped_ex == stripped_url or stripped_url.startswith(stripped_ex + "/")):
                is_excluded = True
                break

        if is_excluded:
            error_logger.info("Skipping excluded URL: %s", url)
            supabase.table("crawling_tasks").update({"status": CrawlingStatus.COMPLETED.value}).eq("id", task_id).execute()
            return

        supabase.table("crawling_tasks").update({"status": CrawlingStatus.IN_PROGRESS.value}).eq("id", task_id).execute()
        error_logger.info("Crawling URL: %s at depth %s", url, depth)

        # 3. Resolve crawl mode
        crawl_mode_resp = supabase.table("tenants").select("crawl_mode").eq("id", str(tenant_id)).single().execute()
        crawl_mode = (crawl_mode_resp.data or {}).get("crawl_mode") or "playwright_llm"

        # ---------------------------------------------------------------
        # SOUP MODE
        # ---------------------------------------------------------------
        if crawl_mode == "soup":
            error_logger.info("crawl_mode=soup for %s — skipping Playwright", url)

            html, status_code = fetch_html(url)
            if not html or status_code >= 400:
                supabase.table("crawling_tasks").update({"status": CrawlingStatus.FAILED.value}).eq("id", task_id).execute()
                supabase.table("tenant_sources").insert({
                    "tenant_id": str(tenant_id), "source_type": "URL",
                    "source_location": url, "status": "ERROR", "status_code": status_code,
                }).execute()
                return

            source_response = supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": "URL",
                "source_location": url, "status": "PROCESSING", "status_code": status_code,
            }).execute()
            source_id = source_response.data[0]["id"]

            docs = asyncio.run(async_fetch_and_chunk_soup(url, source_id, tenant_id))
            if docs:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
                process_documents(docs, tenant_id, embeddings)
                supabase.table("tenant_sources").update({
                    "status": "COMPLETED", "chunk_count": len(docs),
                }).eq("id", source_id).execute()

            # Discover + enqueue links
            found_links = set(extract_internal_links(html, url))
            if depth < max_depth and found_links:
                existing_urls_response = supabase.table("crawling_tasks").select("url").eq("job_id", job_id).execute()
                existing_urls = {item["url"] for item in existing_urls_response.data}
                new_links = found_links - existing_urls
                new_links = {
                    href for href in new_links
                    if not any(
                        (ex := normalize_url(str(ex_url).strip()))
                        and href.replace("https://", "").replace("http://", "").strip("/").startswith(
                            ex.replace("https://", "").replace("http://", "").strip("/")
                        )
                        for ex_url in excluded_urls if ex_url
                    )
                }
                if new_links:
                    supabase.table("crawling_tasks").insert([
                        {"job_id": job_id, "url": link, "depth": depth + 1,
                         "status": CrawlingStatus.PENDING.value, "parent_url": url}
                        for link in new_links
                    ]).execute()

            supabase.table("crawling_tasks").update({"status": CrawlingStatus.COMPLETED.value}).eq("id", task_id).execute()
            error_logger.info("soup: completed %s", url)
            return

        # ---------------------------------------------------------------
        # PLAYWRIGHT / PLAYWRIGHT_LLM MODE
        # ---------------------------------------------------------------
        # Fast-fail check before launching headless browser
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                fast_check = client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SwiftAnswerBot/1.0)"})
                if fast_check.status_code == 404 or fast_check.status_code >= 500:
                    error_logger.info("Fast fail for %s with status %s", url, fast_check.status_code)
                    supabase.table("crawling_tasks").update({"status": CrawlingStatus.FAILED.value}).eq("id", task_id).execute()
                    supabase.table("tenant_sources").insert({
                        "tenant_id": str(tenant_id), "source_type": "URL",
                        "source_location": url, "status": "ERROR", "status_code": fast_check.status_code,
                    }).execute()
                    return
        except Exception as e:
            error_logger.warning("Fast check failed for %s, falling back to crawler: %s", url, e)

        headers = {"Referer": parent_url} if parent_url else {}

        wildcard_excluded_urls = []
        for u in excluded_urls:
            norm = normalize_url(u)
            wildcard_excluded_urls.append(norm)
            wildcard_excluded_urls.append(f"{norm}/*")
        image_exclude_patterns = [f"*{ext}" for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"]]
        wildcard_excluded_urls.extend(image_exclude_patterns)

        dynamic_run_config = CrawlerRunConfig(
            link_preview_config=LinkPreviewConfig(
                exclude_patterns=wildcard_excluded_urls,
                include_internal=True,
            )
        )

        crawl_result = None

        async def crawl_and_close():
            nonlocal crawl_result
            await asyncio.sleep(random.uniform(0.5, 5.0))
            async with AsyncWebCrawler(config=browser_config) as crawler:
                crawl_result = await crawler.arun(url=url, config=dynamic_run_config, headers=headers)

        try:
            asyncio.run(asyncio.wait_for(crawl_and_close(), timeout=70.0))
        except asyncio.TimeoutError:
            error_logger.error("Timeout loading page %s", url)
            supabase.table("crawling_tasks").update({"status": CrawlingStatus.FAILED.value}).eq("id", task_id).execute()
            supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": "URL",
                "source_location": url, "status": "ERROR", "status_code": 408,
            }).execute()
            return

        found_links = set()
        status_code = getattr(crawl_result, "status_code", None) if crawl_result else None

        if crawl_result and crawl_result.success and crawl_result.markdown:
            source_response = supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": "URL",
                "source_location": url, "status": "PROCESSING", "status_code": status_code,
            }).execute()
            source_id = source_response.data[0]["id"]

            from urllib.parse import urlparse
            ext = os.path.splitext(urlparse(crawl_result.url).path)[1].lower() or ".html"
            docs = asyncio.run(get_document_chunks(crawl_result.markdown, crawl_result.url, source_id, ext, tenant_id))
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
            process_documents(docs, tenant_id, embeddings)
            supabase.table("tenant_sources").update({"chunk_count": len(docs)}).eq("id", source_id).execute()

            for link in crawl_result.links.get("internal", []):
                href = normalize_url(link["href"])
                is_excluded_link = False
                for excluded in normalized_excluded_list:
                    if not excluded:
                        continue
                    stripped_ex = excluded.replace("https://", "").replace("http://", "").strip("/")
                    stripped_lnk = href.replace("https://", "").replace("http://", "").strip("/")
                    if stripped_ex and (stripped_ex == stripped_lnk or stripped_lnk.startswith(stripped_ex + "/")):
                        is_excluded_link = True
                        break
                if not is_excluded_link:
                    found_links.add(href)
        else:
            supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": "URL",
                "source_location": url, "status": "ERROR",
                "status_code": status_code if status_code else 500,
            }).execute()

        # Discover new links
        if depth < max_depth:
            existing_urls_response = supabase.table("crawling_tasks").select("url").eq("job_id", job["id"]).execute()
            existing_urls = {item["url"] for item in existing_urls_response.data}
            new_unexcluded_links = found_links - existing_urls
            if new_unexcluded_links:
                supabase.table("crawling_tasks").insert([
                    {"job_id": job["id"], "url": link, "depth": depth + 1,
                     "status": CrawlingStatus.PENDING.value, "parent_url": url}
                    for link in new_unexcluded_links
                ]).execute()

        supabase.table("crawling_tasks").update({"status": CrawlingStatus.COMPLETED.value}).eq("id", task_id).execute()
        error_logger.info("Completed processing URL: %s", url)

    except Exception as e:
        err_str = str(e)
        if "Connection closed" in err_str or "connection closed" in err_str.lower():
            error_logger.warning(
                "Browser connection lost for %s (worker restart?) — task will be re-queued: %s",
                task_details.get("url", "unknown"), err_str,
            )
        else:
            error_logger.error(
                "Error processing URL %s: %s",
                task_details.get("url", "unknown"), err_str, exc_info=True,
            )
        supabase.table("crawling_tasks").update({"status": CrawlingStatus.FAILED.value}).eq("id", task_id).execute()