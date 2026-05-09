"""
tasks/maintenance_tasks.py
Celery Beat periodic tasks — job scheduler and zombie reaper.
"""
from datetime import datetime, timezone, timedelta

from celery import shared_task

from app.database.supabase_client import supabase
from app.data_processing.config import MAX_CONCURRENT_CRAWLS_PER_JOB
from app.models.database import CrawlingStatus
from app.logging_config import error_logger


@shared_task(bind=True, queue="fast")
def job_scheduler_task(self):
    """
    Periodic task — schedules pending crawling tasks and marks completed jobs.
    Acts as the central concurrency controller per job.
    """
    try:
        in_progress_jobs = supabase.table("crawling_jobs").select("*").eq("status", CrawlingStatus.IN_PROGRESS.value).execute().data

        for job in in_progress_jobs:
            job_id = job["id"]
            tenant_id = job["tenant_id"]

            running_count = supabase.table("crawling_tasks").select("id", count="exact").eq("job_id", job_id).eq("status", CrawlingStatus.IN_PROGRESS.value).execute().count

            if running_count == 0:
                pending_count = supabase.table("crawling_tasks").select("id", count="exact").eq("job_id", job_id).eq("status", CrawlingStatus.PENDING.value).execute().count
                if pending_count == 0:
                    error_logger.info("Job %s complete — no remaining tasks.", job_id)
                    supabase.table("crawling_jobs").update({"status": CrawlingStatus.COMPLETED.value}).eq("id", job_id).execute()
                    continue

            if running_count < MAX_CONCURRENT_CRAWLS_PER_JOB:
                limit = MAX_CONCURRENT_CRAWLS_PER_JOB - running_count
                tasks_to_schedule = supabase.table("crawling_tasks").select("*").eq("job_id", job_id).eq("status", CrawlingStatus.PENDING.value).limit(limit).execute().data

                from celery import current_app as celery_app
                for task in tasks_to_schedule:
                    error_logger.debug("Scheduler: Enqueuing task %s for job %s.", task["id"], job_id)
                    celery_app.send_task(
                        "app.data_processing.tasks.crawl_tasks.process_single_url_task",
                        kwargs={
                            "task_id": task["id"],
                            "tenant_id": str(tenant_id),
                            "parent_url": task.get("parent_url"),
                        },
                        queue="heavy",
                    )

    except Exception as e:
        error_logger.error("Error in job_scheduler_task: %s", e, exc_info=True)


@shared_task(bind=True, queue="fast")
def zombie_reaper_task(self):
    """
    Periodic Celery Beat task — finds tenant_sources rows stuck in PROCESSING
    for longer than ZOMBIE_THRESHOLD_HOURS and marks them as ERROR.
    """
    ZOMBIE_THRESHOLD_HOURS = 4
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=ZOMBIE_THRESHOLD_HOURS)).isoformat()
        response = supabase.table("tenant_sources").select("id, tenant_id, source_location, created_at").eq("status", "PROCESSING").lt("created_at", cutoff).execute()
        zombies = response.data or []

        if not zombies:
            error_logger.debug("zombie_reaper: no stuck sources found.")
            return

        zombie_ids = [z["id"] for z in zombies]
        error_logger.warning(
            "zombie_reaper: found %d stuck PROCESSING source(s) older than %dh — marking ERROR. ids=%s",
            len(zombie_ids), ZOMBIE_THRESHOLD_HOURS, zombie_ids,
        )
        supabase.table("tenant_sources").update({"status": "ERROR"}).in_("id", zombie_ids).execute()
        error_logger.info("zombie_reaper: successfully marked %d source(s) as ERROR.", len(zombie_ids))

    except Exception as e:
        error_logger.error("zombie_reaper: unexpected error: %s", e, exc_info=True)
