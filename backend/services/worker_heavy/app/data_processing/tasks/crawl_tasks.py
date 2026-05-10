"""
tasks/crawl_tasks.py
Celery tasks for distributed recursive web crawling.

Replaces ChromaDB/LangChain indexing with Gemini File Search Store uploads.
Crawl4AI still handles JS rendering and markdown extraction — unchanged.
File links discovered during crawl are routed to process_file_url (worker_fast).
"""
import os
import asyncio
import random
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import httpx
from celery import shared_task
from celery import current_app as celery_app
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from app.database.supabase_client import supabase
from app.gemini_store.service import GeminiStoreService, INDEXABLE_FILE_EXTENSIONS
from app.data_processing.crawler import get_crawler, browser_config
from app.data_processing.soup_extractor import fetch_html, extract_internal_links
from app.data_processing.ingestion.utils import normalize_url
from app.models.database import CrawlingStatus, SourceType
from app.logging_config import error_logger


def _is_file_link(url: str) -> bool:
    """Returns True if the URL path ends in an indexable file extension."""
    ext = Path(urlparse(url).path).suffix.lower()
    return ext in INDEXABLE_FILE_EXTENSIONS


def _dispatch_file_url(url: str, tenant_id: str) -> None:
    """
    Creates a FILE_URL source record and dispatches process_file_url to worker_fast.
    Called when a file link is discovered during a Playwright crawl.
    """
    try:
        rec = supabase.table("tenant_sources").insert({
            "tenant_id": tenant_id,
            "source_type": SourceType.FILE_URL.value,
            "source_location": url,
            "status": "QUEUED",
        }).execute()
        source_id = rec.data[0]["id"]
        celery_app.send_task(
            "app.data_processing.tasks.process_file_url",
            args=[url, source_id, tenant_id],
            queue="fast",
        )
        error_logger.info("Dispatched FILE_URL %s (source %s) to worker_fast", url, source_id)
    except Exception as e:
        error_logger.error("Failed to dispatch FILE_URL %s: %s", url, e, exc_info=True)


def _upload_page_to_store(
    markdown: str, url: str, source_id: int, tenant_id: str
) -> None:
    """Uploads crawled markdown to the tenant's File Search Store and marks the source COMPLETED."""
    store_name = GeminiStoreService.get_or_create_store(tenant_id)
    doc_name = GeminiStoreService.upload_text(
        store_name=store_name,
        text=markdown,
        display_name=url,
        metadata={"tenant_id": tenant_id, "source_id": str(source_id), "source_url": url},
    )
    supabase.table("tenant_sources").update({
        "gemini_document_name": doc_name,
        "status": "COMPLETED",
    }).eq("id", source_id).execute()
    error_logger.info("Indexed page %s (source %s) → %s", url, source_id, doc_name)


# ---------------------------------------------------------------------------
# Orchestrator task — creates the job and fires the first crawl task
# ---------------------------------------------------------------------------

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
    Orchestrator task — creates a CrawlingJob and fires the first CrawlingTask.
    Unchanged logic; indexing happens in process_single_url_task.
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
            supabase.table("crawling_jobs").update(
                {"status": CrawlingStatus.FAILED.value}
            ).eq("id", job_id).execute()
        self.update_state(state="FAILURE", meta={"status": error_message})
        raise e


# ---------------------------------------------------------------------------
# Worker task — crawls a single URL, indexes it, discovers next links
# ---------------------------------------------------------------------------

@shared_task(bind=True, queue="heavy", time_limit=600)
def process_single_url_task(self, task_id: int, tenant_id: UUID, parent_url: str = None):
    """
    Crawls one URL with Playwright (via Crawl4AI), uploads the markdown to
    the Gemini File Search Store, then discovers and enqueues child links.

    File links found during discovery are dispatched to process_file_url (worker_fast)
    and shown as FILE_URL sources in the UI.
    """
    task_details = {}
    try:
        task_response = (
            supabase.table("crawling_tasks")
            .select("*, crawling_jobs(*)")
            .eq("id", task_id)
            .execute()
        )
        if not task_response.data:
            error_logger.debug("Task %s not found — job deleted while queued, discarding.", task_id)
            return

        task_details = task_response.data[0]
        job = task_details["crawling_jobs"]
        job_id = job["id"]
        url = task_details["url"]
        depth = task_details["depth"]
        max_depth = job["max_depth"]
        excluded_urls = job.get("excluded_urls", [])

        normalized_url = normalize_url(url)
        normalized_excluded_list = [normalize_url(str(ex).strip()) for ex in excluded_urls]

        # ------------------------------------------------------------------
        # Exclusion check
        # ------------------------------------------------------------------
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
            supabase.table("crawling_tasks").update(
                {"status": CrawlingStatus.COMPLETED.value}
            ).eq("id", task_id).execute()
            return

        supabase.table("crawling_tasks").update(
            {"status": CrawlingStatus.IN_PROGRESS.value}
        ).eq("id", task_id).execute()
        error_logger.info("Crawling URL: %s at depth %s", url, depth)

        # ------------------------------------------------------------------
        # Resolve crawl mode
        # ------------------------------------------------------------------
        crawl_mode_resp = (
            supabase.table("tenants")
            .select("crawl_mode")
            .eq("id", str(tenant_id))
            .single()
            .execute()
        )
        crawl_mode = (crawl_mode_resp.data or {}).get("crawl_mode") or "playwright_llm"

        # ==================================================================
        # SOUP MODE — httpx + trafilatura, no Playwright
        # ==================================================================
        if crawl_mode == "soup":
            error_logger.info("crawl_mode=soup for %s", url)

            html, status_code = fetch_html(url)
            if not html or status_code >= 400:
                supabase.table("crawling_tasks").update(
                    {"status": CrawlingStatus.FAILED.value}
                ).eq("id", task_id).execute()
                supabase.table("tenant_sources").insert({
                    "tenant_id": str(tenant_id), "source_type": SourceType.URL.value,
                    "source_location": url, "status": "ERROR", "status_code": status_code,
                }).execute()
                return

            source_response = supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": SourceType.URL.value,
                "source_location": url, "status": "PROCESSING", "status_code": status_code,
            }).execute()
            source_id = source_response.data[0]["id"]

            import trafilatura
            text = trafilatura.extract(html, url=url, output_format="markdown",
                                       include_links=False, include_images=False)
            if text:
                try:
                    _upload_page_to_store(text, url, source_id, str(tenant_id))
                except Exception as upload_err:
                    error_logger.error("soup: Gemini upload failed for %s (source %s): %s", url, source_id, upload_err, exc_info=True)
                    supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()
            else:
                error_logger.warning("soup: no content extracted from %s", url)
                supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()

            # Link discovery
            found_links: set[str] = set()
            for href in extract_internal_links(html, url):
                _check_and_add_link(href, normalized_excluded_list, found_links,
                                    str(tenant_id), job_id, depth, max_depth, url)

            supabase.table("crawling_tasks").update(
                {"status": CrawlingStatus.COMPLETED.value}
            ).eq("id", task_id).execute()
            error_logger.info("soup: completed %s", url)
            return

        # ==================================================================
        # PLAYWRIGHT / PLAYWRIGHT_LLM MODE — Crawl4AI
        # ==================================================================
        # Fast-fail: HEAD request before launching browser
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                fast_check = client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (compatible; SwiftAnswerBot/1.0)"}
                )
                if fast_check.status_code == 404 or fast_check.status_code >= 500:
                    error_logger.info("Fast-fail %s with status %s", url, fast_check.status_code)
                    supabase.table("crawling_tasks").update(
                        {"status": CrawlingStatus.FAILED.value}
                    ).eq("id", task_id).execute()
                    supabase.table("tenant_sources").insert({
                        "tenant_id": str(tenant_id), "source_type": SourceType.URL.value,
                        "source_location": url, "status": "ERROR",
                        "status_code": fast_check.status_code,
                    }).execute()
                    return
        except Exception as e:
            error_logger.warning("Fast-check failed for %s, falling back to crawler: %s", url, e)

        headers = {"Referer": parent_url} if parent_url else {}
        dynamic_run_config = CrawlerRunConfig(wait_until="load", page_timeout=60000, verbose=False)
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
            supabase.table("crawling_tasks").update(
                {"status": CrawlingStatus.FAILED.value}
            ).eq("id", task_id).execute()
            supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": SourceType.URL.value,
                "source_location": url, "status": "ERROR", "status_code": 408,
            }).execute()
            return

        found_links: set[str] = set()
        status_code = getattr(crawl_result, "status_code", None) if crawl_result else None

        if crawl_result and crawl_result.success and crawl_result.markdown:
            # Create source record and upload markdown to File Search
            source_response = supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": SourceType.URL.value,
                "source_location": url, "status": "PROCESSING", "status_code": status_code,
            }).execute()
            source_id = source_response.data[0]["id"]

            try:
                _upload_page_to_store(crawl_result.markdown, url, source_id, str(tenant_id))
            except Exception as upload_err:
                error_logger.error(
                    "playwright: Gemini upload failed for %s (source %s): %s",
                    url, source_id, upload_err, exc_info=True
                )
                supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()

            # Link discovery — use Crawl4AI's pre-filtered internal link list.
            # Do NOT use raw BS4 on rendered_html: it picks up every <a> tag
            # (nav, footer, JS-modal links) and generates hundreds of spurious URLs.
            for lnk in crawl_result.links.get("internal", []):
                href = lnk.get("href", "").split("#")[0].strip()  # strip fragments
                if href:
                    _check_and_add_link(href, normalized_excluded_list, found_links,
                                        str(tenant_id), job_id, depth, max_depth, url)

            error_logger.info("playwright: found %d page links on %s", len(found_links), url)
        else:
            supabase.table("tenant_sources").insert({
                "tenant_id": str(tenant_id), "source_type": SourceType.URL.value,
                "source_location": url, "status": "ERROR",
                "status_code": status_code if status_code else 500,
            }).execute()

        # Enqueue discovered page links (file links already dispatched in _check_and_add_link)
        if depth < max_depth and found_links:
            found_list = list(found_links)

            # Deduplicate within the current job only — URLs already in crawling_tasks
            # for this job_id are skipped. We do NOT check tenant_sources so that
            # re-crawling the same site across separate jobs works correctly.
            tasks_resp = supabase.table("crawling_tasks") \
                .select("url") \
                .eq("job_id", job_id) \
                .in_("url", found_list) \
                .execute()

            already_queued = {item["url"] for item in (tasks_resp.data or [])}
            new_links = found_links - already_queued

            if new_links:
                new_task_rows = supabase.table("crawling_tasks").insert([
                    {
                        "job_id": job_id, "url": link, "depth": depth + 1,
                        "status": CrawlingStatus.PENDING.value, "parent_url": url,
                    }
                    for link in new_links
                ]).execute()
                for new_task in new_task_rows.data:
                    process_single_url_task.apply_async(
                        kwargs={
                            "task_id": new_task["id"],
                            "tenant_id": str(tenant_id),
                            "parent_url": url,
                        },
                        queue="heavy",
                    )

        supabase.table("crawling_tasks").update(
            {"status": CrawlingStatus.COMPLETED.value}
        ).eq("id", task_id).execute()
        error_logger.info("Completed processing URL: %s", url)

    except Exception as e:
        err_str = str(e)
        if "Connection closed" in err_str or "connection closed" in err_str.lower():
            error_logger.warning(
                "Browser connection lost for %s (worker restart?) — task re-queued: %s",
                task_details.get("url", "unknown"), err_str,
            )
        else:
            error_logger.error(
                "Error processing URL %s: %s",
                task_details.get("url", "unknown"), err_str, exc_info=True,
            )
        supabase.table("crawling_tasks").update(
            {"status": CrawlingStatus.FAILED.value}
        ).eq("id", task_id).execute()


# ---------------------------------------------------------------------------
# Internal helper: classify a discovered link
# ---------------------------------------------------------------------------

def _check_and_add_link(
    href: str,
    normalized_excluded_list: list[str],
    found_page_links: set[str],
    tenant_id: str,
    job_id: int,
    depth: int,
    max_depth: int,
    parent_url: str,
) -> None:
    """
    Evaluates a discovered link:
    - Excluded → skip
    - File extension (PDF, DOCX, image, …) → dispatch to process_file_url (worker_fast)
    - HTML page within depth limit → add to found_page_links for later enqueueing
    """
    # Exclusion check
    for excluded in normalized_excluded_list:
        if not excluded:
            continue
        stripped_ex = excluded.replace("https://", "").replace("http://", "").strip("/")
        stripped_lnk = href.replace("https://", "").replace("http://", "").strip("/")
        if stripped_ex and (stripped_ex == stripped_lnk or stripped_lnk.startswith(stripped_ex + "/")):
            return  # excluded

    if _is_file_link(href):
        # File link: dispatch to worker_fast immediately, don't add to crawling_tasks
        _dispatch_file_url(href, tenant_id)
    elif depth < max_depth:
        # Regular HTML page within depth budget
        found_page_links.add(href)