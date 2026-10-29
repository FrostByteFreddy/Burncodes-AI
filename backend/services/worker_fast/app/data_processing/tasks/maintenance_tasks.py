"""
tasks/maintenance_tasks.py
Celery Beat periodic tasks — crawl job watchdog, zombie reaper, weekly re-crawl,
conversation review.
"""
from datetime import datetime, timedelta, timezone

from celery import current_app as celery_app
from celery import shared_task

from app.database.supabase_client import supabase
from app.knowledge import jobs
from app.logging_config import error_logger
from app.models.database import CrawlingStatus

SCAN_TASK = "app.data_processing.tasks.crawl_tasks.process_single_url_task"
CRAWL_TASK = "app.data_processing.tasks.crawl_tasks.crawl_links_task"

# A queued message older than this is presumed lost (worker restart, broker flush)
STALE_ENQUEUE = timedelta(minutes=20)
# Learning that runs longer than this died with its worker (task limit: 15 min)
STALE_LEARNING = timedelta(hours=1)


def _ago(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) - delta).isoformat()


@shared_task(bind=True, queue="fast")
def job_scheduler_task(self):
    """
    Watchdog, every 30 s. Crawl tasks are queued when discovered; this only
    re-sends tasks whose message was evidently lost and finishes jobs whose
    last task died without doing so. It used to re-send every PENDING task on
    every run, which processed waiting pages many times over.
    """
    try:
        scanning = (
            supabase.table("crawling_jobs").select("id, tenant_id")
            .eq("status", CrawlingStatus.IN_PROGRESS.value).execute()
        ).data or []
        for job in scanning:
            lost = (
                supabase.table("crawling_tasks").select("id, parent_url")
                .eq("job_id", job["id"]).eq("status", CrawlingStatus.PENDING.value)
                .or_(f"enqueued_at.is.null,enqueued_at.lt.{_ago(STALE_ENQUEUE)}")
                .limit(200).execute()
            ).data or []
            for task in lost:
                celery_app.send_task(
                    SCAN_TASK,
                    kwargs={"task_id": task["id"], "tenant_id": job["tenant_id"], "parent_url": task.get("parent_url")},
                    queue="heavy",
                )
            if lost:
                supabase.table("crawling_tasks").update({"enqueued_at": jobs.now_iso()}) \
                    .in_("id", [t["id"] for t in lost]).execute()
                error_logger.warning("Scheduler: re-sent %d lost task(s) for job %s", len(lost), job["id"])
            jobs.complete_scan_if_done(job["id"])

        # Learning stalled (nothing processing, sources still queued, confirmed a while ago)
        indexing = (
            supabase.table("crawling_jobs").select("id, confirmed_at")
            .eq("status", CrawlingStatus.INDEXING.value)
            .lt("confirmed_at", _ago(STALE_ENQUEUE)).execute()
        ).data or []
        for job in indexing:
            busy = supabase.table("tenant_sources").select("id").eq("last_job_id", job["id"]) \
                .eq("status", "PROCESSING").limit(1).execute().data
            if busy:
                continue
            queued = supabase.table("tenant_sources").select("id").eq("last_job_id", job["id"]) \
                .eq("status", "QUEUED").limit(500).execute().data or []
            for src in queued:
                celery_app.send_task(jobs.LEARN_TASK, args=[src["id"], job["id"]], queue="fast")
            if queued:
                error_logger.warning("Scheduler: re-sent %d learn task(s) for job %s", len(queued), job["id"])
            jobs.finish_job_if_learned(job["id"])
    except Exception as e:
        error_logger.error("Error in job_scheduler_task: %s", e, exc_info=True)


@shared_task(bind=True, queue="fast")
def zombie_reaper_task(self):
    """
    Sources stuck in PROCESSING (worker died mid-learn) go to ERROR. Their
    content_hash wasn't updated, so the next crawl simply learns them again.
    """
    try:
        zombies = (
            supabase.table("tenant_sources").select("id")
            .eq("status", "PROCESSING").lt("learn_started_at", _ago(STALE_LEARNING))
            .limit(1000).execute()
        ).data or []
        if zombies:
            ids = [z["id"] for z in zombies]
            supabase.table("tenant_sources").update({"status": "ERROR"}).in_("id", ids).execute()
            error_logger.warning("zombie_reaper: marked %d stuck source(s) as ERROR: %s", len(ids), ids[:20])
    except Exception as e:
        error_logger.error("zombie_reaper: unexpected error: %s", e, exc_info=True)


@shared_task(bind=True, queue="fast")
def weekly_recrawl_task(self):
    """
    Tenants with auto_recrawl: re-run each crawl whose latest run is older
    than the tenant's interval. Scheduled jobs are pre-approved (auto_confirm,
    capped by RECRAWL_AUTO_CONFIRM_MAX_CHF); unchanged pages cost nothing.
    """
    try:
        tenants = (
            supabase.table("tenants").select("id, recrawl_interval_days").eq("auto_recrawl", True).execute()
        ).data or []
        for tenant in tenants:
            tenant_jobs = (
                supabase.table("crawling_jobs")
                .select("start_url, status, created_at, max_depth, single_page_only, excluded_urls, same_language, use_sitemap, skip_funnel, learning_model, crawl_mode")
                .eq("tenant_id", tenant["id"]).order("created_at", desc=True).limit(500).execute()
            ).data or []
            active = {CrawlingStatus.IN_PROGRESS.value, CrawlingStatus.SCANNED.value, CrawlingStatus.INDEXING.value}
            if any(j["status"] in active for j in tenant_jobs):
                continue  # one thing at a time per tenant
            latest: dict[str, dict] = {}
            for j in tenant_jobs:
                latest.setdefault(j["start_url"], j)
            cutoff = _ago(timedelta(days=tenant.get("recrawl_interval_days") or 7))
            for start_url, j in latest.items():
                if j["created_at"] >= cutoff:
                    continue
                celery_app.send_task(CRAWL_TASK, kwargs={
                    "tenant_id": tenant["id"],
                    "start_url": start_url,
                    "single_page_only": j.get("single_page_only") or False,
                    "excluded_urls": j.get("excluded_urls") or [],
                    "same_language": j.get("same_language") or False,
                    "use_sitemap": j.get("use_sitemap") or False,
                    "skip_funnel": j.get("skip_funnel") or False,
                    "max_depth": j.get("max_depth") or 3,
                    "trigger": "scheduled",
                    "auto_confirm": True,
                    "crawl_mode": j.get("crawl_mode"),
                }, queue="heavy")
                error_logger.info("weekly_recrawl: re-crawling %s for tenant %s", start_url, tenant["id"])
                break  # at most one crawl per tenant per run
    except Exception as e:
        error_logger.error("weekly_recrawl_task: unexpected error: %s", e, exc_info=True)


@shared_task(bind=True, queue="fast", soft_time_limit=1500, time_limit=1800)
def review_conversations_task(self, tenant_id=None):
    """
    Nightly (or on demand for one tenant): review conversations that went quiet
    and were never reviewed, store what staff should act on, and bill the owner
    per reviewed conversation.
    """
    from app.billing.services import BillingService
    from app.knowledge import review

    try:
        query = (supabase.table("tenants").select("id, user_id, review_interval_days, last_review_at")
                 .eq("review_chats", True).eq("is_active", True))
        if tenant_id:
            query = query.eq("id", str(tenant_id))
        tenants = query.execute().data or []
        now = datetime.now(timezone.utc)
        for tenant in tenants:
            # The nightly run only picks tenants whose interval is up; "Review now" always runs.
            # An hour of slack keeps a daily schedule from drifting by a day.
            interval = timedelta(days=tenant.get("review_interval_days") or 1) - timedelta(hours=1)
            if not tenant_id and tenant.get("last_review_at") and _ago(interval) < tenant["last_review_at"]:
                continue
            if BillingService.check_balance(tenant["user_id"]) <= 0:
                continue
            supabase.table("tenants").update({"last_review_at": now.isoformat()}).eq("id", tenant["id"]).execute()
            result = review.review_tenant(
                tenant["id"], tenant["user_id"],
                lambda owner, i, o: BillingService.deduct_cost(owner, "review", i, o),
            )
            if result["reviewed"]:
                error_logger.info("review: tenant %s — %d conversations, %d findings",
                                  tenant["id"], result["reviewed"], result["findings"])
    except Exception as e:
        error_logger.error("review_conversations_task: unexpected error: %s", e, exc_info=True)
