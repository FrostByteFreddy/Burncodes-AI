"""
data_processing/tasks/__init__.py
Re-exports all Celery tasks so external imports (celery_worker.py, sources.py)
don't need to change their import paths.
"""
from app.data_processing.tasks.crawl_tasks import crawl_links_task, process_single_url_task  # noqa: F401
from app.data_processing.tasks.maintenance_tasks import job_scheduler_task, zombie_reaper_task  # noqa: F401

__all__ = [
    "crawl_links_task",
    "process_single_url_task",
    "job_scheduler_task",
    "zombie_reaper_task",
]
