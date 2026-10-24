"""
worker_fast/app/data_processing/tasks/__init__.py

Fast-queue Celery tasks: learning (Gemini understanding + indexing) and
uploads. Crawling/scanning runs in worker_heavy; the job lifecycle lives in
app.knowledge.jobs.
"""
from celery import shared_task

from app.database.supabase_client import supabase
from app.knowledge import jobs
from app.knowledge.learn import MAX_FILE_BYTES, learn_source
from app.knowledge.markdown import content_hash, pdf_page_count
from app.data_processing.tasks.maintenance_tasks import (  # noqa: F401
    job_scheduler_task,
    weekly_recrawl_task,
    zombie_reaper_task,
)
from app.logging_config import error_logger


@shared_task(name="app.data_processing.tasks.learn_source_task", queue="fast", time_limit=900, soft_time_limit=870)
def learn_source_task(source_id: int, job_id: int | None = None):
    """Gemini reads one new/changed source and indexes what it understood."""
    learn_source(source_id, job_id)


@shared_task(name="app.data_processing.tasks.start_learning_task", queue="fast")
def start_learning_task(job_id: int):
    """Sent by the API when the user confirms a scanned crawl's estimate."""
    jobs.start_learning(job_id)


@shared_task(name="app.data_processing.tasks.process_local_file", queue="fast", time_limit=900, soft_time_limit=870)
def process_local_file(file_path: str, source_filename: str, source_id: int, tenant_id: str):
    """
    An uploaded file: fingerprint it, then learn it right away (the user
    explicitly chose this one file, so there's no separate confirmation step).
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read(MAX_FILE_BYTES + 1)
    except OSError as e:
        error_logger.error("Upload %s unreadable: %s", file_path, e)
        supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()
        return
    supabase.table("tenant_sources").update({
        "pending_hash": content_hash(data),
        "file_pages": pdf_page_count(data) if source_filename.lower().endswith(".pdf") else 1,
        "title": source_filename[:500],
        "last_seen_at": jobs.now_iso(),
    }).eq("id", source_id).execute()
    learn_source(source_id, None)


__all__ = [
    "learn_source_task",
    "start_learning_task",
    "process_local_file",
    "job_scheduler_task",
    "weekly_recrawl_task",
    "zombie_reaper_task",
]
