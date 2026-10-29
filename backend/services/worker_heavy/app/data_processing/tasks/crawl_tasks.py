"""
tasks/crawl_tasks.py
Scan phase of the crawl pipeline (job lifecycle: app.knowledge.jobs).

Each task fetches one URL, converts it to Markdown (pages) or hashes its bytes
(files), records the result on the tenant's single source row for that URL,
and queues newly discovered links. No LLM runs here — learning happens after
the user confirmed the estimate (worker_fast, learn_source_task).

Duplicate protection:
  - a task is claimed with a conditional UPDATE (PENDING → IN_PROGRESS); a
    second copy of the same message finds nothing to claim and exits
  - links are inserted with ON CONFLICT (job_id, url) DO NOTHING and only the
    rows actually inserted are queued — each URL is visited once per job
"""
import re
import os
import time
import asyncio
import random
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import UUID

import httpx
from celery import shared_task
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from app.billing.services import BillingService
from app.data_processing.crawler import browser_config
from app.data_processing.ingestion.utils import normalize_url
from app.data_processing.soup_extractor import HEADERS, extract_internal_links, fetch_html
from app.database.supabase_client import supabase
from app.gemini_store.service import INDEXABLE_FILE_EXTENSIONS, UNSUPPORTED_EXTENSIONS
from app.knowledge import jobs
from app.ai_models import INDEXING_GEMINI_MODEL, count_tokens
from app.knowledge.markdown import content_hash, estimate_tokens, html_to_markdown, pdf_page_count, contact_from_link
from app.knowledge.url_scope import is_excluded, is_funnel_page, other_language, site as _site
from app.logging_config import error_logger
from app.models.database import CrawlingStatus, SourceType
from app.security.url_guard import UnsafeURLError, is_public_url, safe_client

MAX_FILE_BYTES = 50 * 1024 * 1024
# Pages with less text than this carry nothing worth learning
MIN_CONTENT_TOKENS = 20
_INSERT_BATCH = 200


# Linked documents worth learning even on "this page only" crawls (not images)
_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}


def _is_file_link(url: str) -> bool:
    ext = Path(urlparse(url).path).suffix.lower()
    return ext in INDEXABLE_FILE_EXTENSIONS or ext in UNSUPPORTED_EXTENSIONS


def _canonical_link(href: str) -> str:
    """
    Normalised URL for de-duplication. File links drop their query string:
    CMSs append cache-busters (…/Abfallkalender_2026.pdf?fp=1764757298475)
    that would otherwise turn one file into many sources.
    """
    url = normalize_url(href.split("#")[0].strip())
    if _is_file_link(url):
        url = url.split("?", 1)[0]
    return url


def _is_contact_link(url: str) -> bool:
    """Email/phone links (also ones hidden in the path) aren't pages; their address is kept in the page text."""
    return contact_from_link(url) is not None


def _finish_task(task_id: int, status: CrawlingStatus, outcome: str) -> None:
    supabase.table("crawling_tasks").update({"status": status.value, "outcome": outcome}).eq("id", task_id).execute()


def _enqueue(task_rows: list[dict], tenant_id: str) -> None:
    for row in task_rows:
        process_single_url_task.apply_async(
            kwargs={"task_id": row["id"], "tenant_id": tenant_id, "parent_url": row.get("parent_url")},
            queue="heavy",
        )
    ids = [r["id"] for r in task_rows]
    for i in range(0, len(ids), _INSERT_BATCH):
        supabase.table("crawling_tasks").update({"enqueued_at": jobs.now_iso()}).in_("id", ids[i:i + _INSERT_BATCH]).execute()


def _add_links(job: dict, tenant_id: str, depth: int, parent_url: str, hrefs: list[str]) -> int:
    """Inserts unseen links as tasks of this job and queues them. Returns how many were new."""
    start_site = _site(urlparse(job["start_url"]).hostname)
    excluded = job.get("excluded_urls") or []
    max_depth = job["max_depth"]
    rows, seen = [], set()
    for href in hrefs:
        url = _canonical_link(href)
        parsed = urlparse(url)
        if not url or url in seen or parsed.scheme not in ("http", "https"):
            continue
        if start_site and _site(parsed.hostname) != start_site:
            continue  # same site only — no drifting into other subdomains
        if parsed.scheme == "http" and urlparse(job["start_url"]).scheme == "https":
            # the same page linked as http:// and https:// would be read twice
            url = "https://" + url[len("http://"):]
            if url in seen:
                continue
        if is_excluded(url, excluded) or _is_contact_link(url):
            continue
        if job.get("same_language") and other_language(url, job["start_url"]):
            continue  # the bot answers in any language: one language version is enough
        if job.get("skip_funnel") and is_funnel_page(url):
            continue
        if _is_file_link(url):
            if max_depth <= 1 and Path(parsed.path).suffix.lower() not in _DOCUMENT_EXTENSIONS:
                continue  # "this page only": its documents, but not images
        elif depth >= max_depth:
            continue
        seen.add(url)
        rows.append({"job_id": job["id"], "url": url, "depth": depth + 1,
                     "status": CrawlingStatus.PENDING.value, "parent_url": parent_url})

    inserted = []
    for i in range(0, len(rows), _INSERT_BATCH):
        inserted += (
            supabase.table("crawling_tasks")
            .upsert(rows[i:i + _INSERT_BATCH], on_conflict="job_id,url", ignore_duplicates=True)
            .execute()
        ).data or []
    if inserted:
        _enqueue(inserted, tenant_id)
    return len(inserted)


def _add_sitemap_pages(job: dict, tenant_id: str, start_url: str) -> None:
    """
    Whole-site crawls also visit what the sitemap lists below the start
    address: landing pages no menu links to. They're read at the deepest
    level, so they don't lead further. Never fails the scan.
    """
    if not job.get("use_sitemap") or job["max_depth"] <= 1:
        return
    try:
        from app.knowledge.sitemap import sitemap_urls
        below = urlparse(job["start_url"]).path.rstrip("/")
        urls = [u for u in sitemap_urls(job["start_url"])
                if not below or urlparse(u).path.rstrip("/") == below or urlparse(u).path.startswith(below + "/")]
        found = _add_links(job, tenant_id, job["max_depth"] - 1, start_url, urls)
        jobs.log_event(job["id"], tenant_id, "sitemap_read", url=start_url, listed=len(urls), count=found)
    except Exception as e:
        error_logger.warning("sitemap of %s skipped: %s", job["start_url"], e)


def _record_error(tenant_id: str, url: str, source_type: str, job_id: int, status_code: int) -> None:
    """
    Records a failed fetch. A source that was indexed before keeps its content
    (its last_job_id isn't touched, so repeated failures count as misses and
    eventually remove it); unknown URLs get an ERROR row for the report.
    """
    existing = jobs.get_source(tenant_id, url)
    if existing and existing.get("status") == "COMPLETED":
        return
    fields = {"status": "ERROR", "status_code": status_code, "last_job_id": job_id, "last_seen_at": jobs.now_iso()}
    if existing:
        supabase.table("tenant_sources").update(fields).eq("id", existing["id"]).execute()
    else:
        supabase.table("tenant_sources").insert(
            {**fields, "tenant_id": tenant_id, "source_location": url, "source_type": source_type}
        ).execute()


# ---------------------------------------------------------------------------
# Politeness: one website, one request at a time, at a steady pace
# ---------------------------------------------------------------------------
# All scan workers share these slots through Redis, so 5 workers don't hit one
# server five times at once. A website that answers "too many requests" gets a
# slower pace for an hour and the page is retried instead of failing.

HOST_INTERVAL_MS = int(os.getenv("CRAWL_HOST_INTERVAL_MS", "1000"))
MAX_HOST_INTERVAL_MS = 10_000
RATE_LIMIT_RETRIES = 4

# reserve the next free slot for a host; returns how long to wait (ms)
_RESERVE_SLOT = """
local now = tonumber(ARGV[1])
local interval = tonumber(redis.call('GET', KEYS[2]) or ARGV[2])
local slot = math.max(now, tonumber(redis.call('GET', KEYS[1]) or 0))
redis.call('SET', KEYS[1], slot + interval, 'PX', 600000)
return slot - now
"""

_redis = None


def _redis_client():
    global _redis
    if _redis is None:
        import redis
        _redis = redis.Redis.from_url(os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"))
    return _redis


def _wait_for_host(url: str) -> None:
    host = _site(urlparse(url).hostname)
    try:
        wait_ms = _redis_client().eval(_RESERVE_SLOT, 2, f"crawl:next:{host}", f"crawl:interval:{host}",
                                       int(time.time() * 1000), HOST_INTERVAL_MS)
    except Exception as e:
        error_logger.debug("crawl throttle unavailable: %s", e)
        return  # best effort: never block a crawl on Redis
    if wait_ms and wait_ms > 0:
        time.sleep(min(int(wait_ms), 120_000) / 1000)


def _slow_down(url: str) -> None:
    """The website pushed back: double the pause between requests to it (for an hour)."""
    host = _site(urlparse(url).hostname)
    key = f"crawl:interval:{host}"
    try:
        r = _redis_client()
        current = int(r.get(key) or HOST_INTERVAL_MS)
        r.set(key, min(MAX_HOST_INTERVAL_MS, current * 2), ex=3600)
    except Exception:
        pass


class RateLimited(Exception):
    """The website answered 429/503 or not at all: try this page again later."""

    def __init__(self, retry_after: int | None = None, status_code: int = 429):
        super().__init__(f"try later (status {status_code}, retry after {retry_after})")
        self.retry_after = retry_after
        self.status_code = status_code   # recorded if the last attempt fails too


def _retry_after(headers) -> int | None:
    try:
        value = int((headers or {}).get("retry-after", ""))
        return value if 0 < value <= 3600 else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def _fetch_playwright(url: str, parent_url: str | None) -> tuple[str | None, int, list[str]]:
    """Renders the page. Returns (html, status_code, internal links). Raises UnsafeURLError."""
    # Fast-fail before launching a browser; the guard also checks every redirect hop.
    _wait_for_host(url)
    with safe_client(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
        check = client.get(url)
    if check.status_code in (429, 503):
        raise RateLimited(_retry_after(check.headers))
    if check.status_code == 404 or check.status_code >= 500:
        return None, check.status_code, []

    result = None

    async def crawl():
        nonlocal result
        await asyncio.sleep(random.uniform(0.5, 3.0))
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(wait_until="load", page_timeout=60000, verbose=False),
                headers={"Referer": parent_url} if parent_url else {},
            )

    try:
        asyncio.run(asyncio.wait_for(crawl(), timeout=70.0))
    except asyncio.TimeoutError:
        raise RateLimited(status_code=408)
    if not result or not result.success:
        if getattr(result, "status_code", None) in (429, 503):
            raise RateLimited()
        return None, getattr(result, "status_code", None) or 500, []
    redirected = getattr(result, "redirected_url", None)
    if redirected and redirected != url and not is_public_url(redirected):
        raise UnsafeURLError(f"redirected to non-public {redirected}")
    links = [l.get("href", "") for l in (result.links or {}).get("internal", [])]
    return result.html, getattr(result, "status_code", None) or 200, links


def _fetch_soup(url: str) -> tuple[str | None, int, list[str]]:
    _wait_for_host(url)
    html, status = fetch_html(url)
    if status in (429, 503):
        raise RateLimited()
    if not html:
        return None, status, []
    return html, status, extract_internal_links(html, url)


def _fetch_file(url: str, previous: dict | None) -> tuple[bytes | None, int, dict]:
    """Downloads a file; sends ETag/Last-Modified so unchanged files come back as 304."""
    headers = dict(HEADERS)
    if previous and previous.get("status") == "COMPLETED":
        if previous.get("etag"):
            headers["If-None-Match"] = previous["etag"]
        if previous.get("last_modified"):
            headers["If-Modified-Since"] = previous["last_modified"]
    _wait_for_host(url)
    with safe_client(timeout=60.0, follow_redirects=True, headers=headers) as client:
        with client.stream("GET", url) as resp:
            if resp.status_code in (429, 503):
                raise RateLimited(_retry_after(resp.headers))
            meta = {"etag": resp.headers.get("etag"), "last_modified": resp.headers.get("last-modified")}
            if resp.status_code == 304 or resp.status_code >= 400:
                return None, resp.status_code, meta
            data = b""
            for chunk in resp.iter_bytes():
                data += chunk
                if len(data) > MAX_FILE_BYTES:
                    return None, 413, meta
    return data, resp.status_code, meta


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@shared_task(bind=True, queue="fast")
def crawl_links_task(
    self,
    tenant_id: UUID,
    start_url: str,
    single_page_only: bool = False,
    excluded_urls: list[str] = None,
    same_language: bool = False,
    use_sitemap: bool = False,
    skip_funnel: bool = False,
    learning_model: str | None = None,
    max_depth: int = 3,
    trigger: str = "manual",
    auto_confirm: bool = False,
    crawl_mode: str | None = None,
):
    """Creates the crawl job and queues the start URL."""
    start_url = normalize_url(start_url)
    if not crawl_mode:
        row = supabase.table("tenants").select("crawl_mode").eq("id", str(tenant_id)).limit(1).execute().data
        crawl_mode = (row[0].get("crawl_mode") if row else None) or "playwright"
    job = supabase.table("crawling_jobs").insert({
        "tenant_id": str(tenant_id),
        "start_url": start_url,
        "max_depth": 1 if single_page_only else max_depth,
        "single_page_only": single_page_only,
        "status": CrawlingStatus.IN_PROGRESS.value,
        "excluded_urls": excluded_urls or [],
        "same_language": bool(same_language),
        "use_sitemap": bool(use_sitemap),
        "skip_funnel": bool(skip_funnel),
        "learning_model": learning_model,
        "crawl_mode": crawl_mode,
        "trigger": trigger,
        "auto_confirm": auto_confirm,
    }).execute().data[0]
    task = supabase.table("crawling_tasks").insert({
        "job_id": job["id"], "url": start_url, "depth": 1, "status": CrawlingStatus.PENDING.value,
    }).execute().data[0]
    jobs.log_event(job["id"], str(tenant_id), "job_started", url=start_url, trigger=trigger,
                   single_page_only=single_page_only)
    _enqueue([task], str(tenant_id))
    return {"status": "Crawl initiated", "job_id": job["id"]}


@shared_task(bind=True, queue="heavy", time_limit=600)
def process_single_url_task(self, task_id: int, tenant_id: UUID, parent_url: str = None):
    tenant_id = str(tenant_id)
    claimed = (
        supabase.table("crawling_tasks")
        .update({"status": CrawlingStatus.IN_PROGRESS.value})
        .eq("id", task_id).eq("status", CrawlingStatus.PENDING.value)
        .execute()
    ).data
    if not claimed:
        return  # already handled by another copy of this message, or job deleted
    task = claimed[0]
    job_id = task["job_id"]
    url = task["url"]

    try:
        job_rows = supabase.table("crawling_jobs").select("*").eq("id", job_id).limit(1).execute().data
        if not job_rows or job_rows[0]["status"] != CrawlingStatus.IN_PROGRESS.value:
            _finish_task(task_id, CrawlingStatus.FAILED, "cancelled")
            return
        job = job_rows[0]

        if not is_public_url(url):
            _record_error(tenant_id, url, SourceType.URL.value, job_id, 403)
            _finish_task(task_id, CrawlingStatus.FAILED, "refused")
            return
        if not BillingService.tenant_has_balance(tenant_id):
            _finish_task(task_id, CrawlingStatus.FAILED, "no_balance")
            return

        jobs.log_event(job_id, tenant_id, "scan", url=url)
        info = {}  # the scan fills in what it learned about the page, e.g. its title
        if _is_file_link(url):
            outcome = _scan_file(tenant_id, url, job_id, info)
        else:
            outcome = _scan_page(tenant_id, url, job, task["depth"], parent_url, info)
        jobs.log_event(job_id, tenant_id, "scanned", url=url, outcome=outcome, title=info.get("title"))
        status = CrawlingStatus.FAILED if outcome in ("error", "refused") else CrawlingStatus.COMPLETED
        _finish_task(task_id, status, outcome)

    except (httpx.TimeoutException, httpx.NetworkError) as e:
        # no answer at all: as with "too many requests", try again later
        _retry_later(task, tenant_id, parent_url, RateLimited(status_code=408 if isinstance(e, httpx.TimeoutException) else 0))
    except RateLimited as e:
        _retry_later(task, tenant_id, parent_url, e)
    except UnsafeURLError as e:
        error_logger.warning("Refusing %s: %s", url, e)
        _record_error(tenant_id, url, SourceType.URL.value, job_id, 403)
        _finish_task(task_id, CrawlingStatus.FAILED, "refused")
        jobs.log_event(job_id, tenant_id, "scanned", url=url, outcome="refused")
    except Exception as e:
        error_logger.error("Scanning %s failed: %s", url, e, exc_info=True)
        _record_error(tenant_id, url, SourceType.URL.value, job_id, 500)
        _finish_task(task_id, CrawlingStatus.FAILED, "error")
        jobs.log_event(job_id, tenant_id, "scanned", url=url, outcome="error")
    finally:
        jobs.complete_scan_if_done(job_id)


def _retry_later(task: dict, tenant_id: str, parent_url: str | None, e: RateLimited) -> None:
    """Re-queues the page with a growing pause; after RATE_LIMIT_RETRIES it counts as failed."""
    task_id, job_id, url = task["id"], task["job_id"], task["url"]
    _slow_down(url)
    attempts = (task.get("attempts") or 0) + 1
    if attempts <= RATE_LIMIT_RETRIES:
        delay = min(600, e.retry_after or 30 * 2 ** (attempts - 1))
        supabase.table("crawling_tasks").update({
            "status": CrawlingStatus.PENDING.value, "attempts": attempts, "enqueued_at": jobs.now_iso(),
        }).eq("id", task_id).execute()
        process_single_url_task.apply_async(
            kwargs={"task_id": task_id, "tenant_id": tenant_id, "parent_url": parent_url},
            countdown=delay, queue="heavy",
        )
        error_logger.info("No answer from %s (%s), retry %d in %ds", url, e.status_code, attempts, delay)
    else:
        outcome = "rate_limited" if e.status_code in (429, 503) else "timeout"
        _record_error(tenant_id, url, SourceType.URL.value, job_id, e.status_code)
        _finish_task(task_id, CrawlingStatus.FAILED, outcome)
        jobs.log_event(job_id, tenant_id, "scanned", url=url, outcome=outcome)


def _seen_in_this_crawl(tenant_id: str, job_id: int, url: str, digest: str) -> bool:
    """
    Same content under another address in this crawl: www/non-www, page-ID
    routes (/route/…/page/75), tracking parameters. Read once, not twice.
    """
    rows = (
        supabase.table("tenant_sources").select("source_location")
        .eq("tenant_id", tenant_id).eq("last_job_id", job_id).eq("pending_hash", digest)
        .neq("source_location", url).limit(1).execute()
    ).data
    return bool(rows)


def _update_contact_card(tenant_id: str, job: dict, url: str, html: str) -> None:
    """
    The start page's footer → the chatbot's contact card (address, phone,
    opening hours). Gemini reads it only when the footer changed. Never fails
    the scan.
    """
    try:
        from app.knowledge.contact import extract_contact
        from app.knowledge.markdown import footer_markdown
        footer = footer_markdown(html)
        digest = content_hash(footer) if footer else ""
        row = supabase.table("tenants").select("contact_footer_hash").eq("id", tenant_id).limit(1).execute().data
        if not footer or (row and row[0].get("contact_footer_hash") == digest):
            return
        card = extract_contact(footer, url)
        fields = {"contact_footer_hash": digest}
        if card:
            fields["contact_card"] = {**card, "source_url": url, "updated_at": jobs.now_iso()}
            jobs.log_event(job["id"], tenant_id, "contact_found", url=url,
                           hours=len(card.get("opening_hours") or []))
        supabase.table("tenants").update(fields).eq("id", tenant_id).execute()
    except Exception as e:
        error_logger.warning("contact card for %s skipped: %s", url, e)


def _scan_page(tenant_id: str, url: str, job: dict, depth: int, parent_url: str | None, info: dict | None = None) -> str:
    mode = job.get("crawl_mode") or "playwright"
    html, status_code, links = _fetch_soup(url) if mode == "soup" else _fetch_playwright(url, parent_url)
    if not html or status_code >= 400:
        _record_error(tenant_id, url, SourceType.URL.value, job["id"], status_code or 500)
        return "error"

    found = _add_links(job, tenant_id, depth, url, links)
    if found:
        jobs.log_event(job["id"], tenant_id, "links_found", url=url, count=found)

    title, markdown = html_to_markdown(html)
    if info is not None and title:
        info["title"] = title[:200]
    if depth == 1:
        _update_contact_card(tenant_id, job, url, html)
        _add_sitemap_pages(job, tenant_id, url)
    tokens = estimate_tokens(markdown)
    if tokens >= MIN_CONTENT_TOKENS:
        # exact size for the cost estimate (free call); the guess only as fallback
        tokens = count_tokens([markdown], INDEXING_GEMINI_MODEL) or tokens
    if tokens < MIN_CONTENT_TOKENS:
        _record_error(tenant_id, url, SourceType.URL.value, job["id"], 204)
        return "empty"
    digest = content_hash(markdown)
    if _seen_in_this_crawl(tenant_id, job["id"], url, digest):
        return "duplicate"
    _, outcome = jobs.record_scan(
        tenant_id, url, SourceType.URL.value, job["id"], digest,
        {"status_code": status_code, "content_markdown": markdown, "content_tokens": tokens, "title": title[:500]},
    )
    return outcome


def _scan_file(tenant_id: str, url: str, job_id: int, info: dict | None = None) -> str:
    ext = Path(urlparse(url).path).suffix.lower()
    if info is not None:
        # the document's name as people see it, e.g. "Abfallkalender 2026"
        info["title"] = unquote(Path(urlparse(url).path).stem).replace("_", " ").replace("-", " ")[:200]
    if ext in UNSUPPORTED_EXTENSIONS:
        return "unsupported"
    previous = jobs.get_source(tenant_id, url)
    data, status_code, meta = _fetch_file(url, previous)
    if status_code == 304 and previous:
        # Unchanged since the last crawl — same hash as what's indexed.
        jobs.record_scan(tenant_id, url, SourceType.FILE_URL.value, job_id, previous.get("content_hash") or "", {})
        return "unchanged"
    if data is None:
        _record_error(tenant_id, url, SourceType.FILE_URL.value, job_id, status_code)
        return "error"
    pages = pdf_page_count(data) if ext == ".pdf" else 1
    digest = content_hash(data)
    if _seen_in_this_crawl(tenant_id, job_id, url, digest):
        return "duplicate"
    _, outcome = jobs.record_scan(
        tenant_id, url, SourceType.FILE_URL.value, job_id, digest,
        {"status_code": status_code, "file_pages": pages, "content_tokens": None,
         "etag": meta.get("etag"), "last_modified": meta.get("last_modified")},
    )
    return outcome
