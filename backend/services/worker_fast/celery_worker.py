"""
services/worker_fast/celery_worker.py
Registers ONLY fast-queue tasks: file ingestion, URL processing, maintenance.
No crawl4ai, no Playwright.
"""
import nest_asyncio
nest_asyncio.apply()

import os
from celery import Celery
from dotenv import load_dotenv
from app.logging_config import error_logger

load_dotenv()

celery = Celery('worker_fast')
celery.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue='fast',
)

# Explicitly import to register @shared_task decorators
import app.data_processing.tasks.maintenance_tasks  # noqa: F401, E402
from app.data_processing.tasks import process_local_file, process_urls  # noqa: F401, E402

error_logger.info("worker_fast: tasks registered — fast queue ready")
