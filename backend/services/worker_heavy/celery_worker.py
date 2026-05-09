"""
services/worker_heavy/celery_worker.py
Registers ONLY heavy-queue tasks: crawl4ai + Playwright URL crawling.
"""
import nest_asyncio
nest_asyncio.apply()

import os
from celery import Celery
from dotenv import load_dotenv
from app.logging_config import error_logger

load_dotenv()

celery = Celery('worker_heavy')
celery.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue='heavy',
    task_routes={
        'app.data_processing.tasks.crawl_tasks.process_single_url_task': {'queue': 'heavy'},
        'app.data_processing.tasks.crawl_tasks.crawl_links_task': {'queue': 'heavy'},
    },
)

# Explicitly import to register @shared_task decorators
import app.data_processing.tasks.crawl_tasks  # noqa: F401, E402

error_logger.info("worker_heavy: tasks registered — heavy queue ready (Playwright enabled)")
