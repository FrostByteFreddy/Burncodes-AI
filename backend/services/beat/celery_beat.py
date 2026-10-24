"""
services/beat/celery_beat.py
Minimal Celery Beat scheduler — sends timed signals to Redis.
NO Flask, NO app imports, NO chromadb, NO langchain.
Total image: ~180MB.
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery = Celery('beat')
celery.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    broker_connection_retry_on_startup=True,
    timezone='UTC',
    enable_utc=True,
    task_default_queue='fast',
    task_routes={
        'app.data_processing.tasks.maintenance_tasks.job_scheduler_task': {'queue': 'fast'},
        'app.data_processing.tasks.maintenance_tasks.zombie_reaper_task': {'queue': 'fast'},
        'app.data_processing.tasks.maintenance_tasks.weekly_recrawl_task': {'queue': 'fast'},
        'app.data_processing.tasks.maintenance_tasks.review_conversations_task': {'queue': 'fast'},
    },
    beat_schedule={
        'job-scheduler-every-30-seconds': {
            # Task name must match the @shared_task registered in worker_fast
            'task': 'app.data_processing.tasks.maintenance_tasks.job_scheduler_task',
            'schedule': 30.0,
        },
        'zombie-reaper-every-30-minutes': {
            'task': 'app.data_processing.tasks.maintenance_tasks.zombie_reaper_task',
            'schedule': 1800.0,
        },
        # Checks every 6 h which opted-in tenants are due (default: weekly)
        'recrawl-check-every-6-hours': {
            'task': 'app.data_processing.tasks.maintenance_tasks.weekly_recrawl_task',
            'schedule': 6 * 3600.0,
        },
        # Reviews conversations that went quiet for unanswered questions and pushback
        'review-conversations-hourly': {
            'task': 'app.data_processing.tasks.maintenance_tasks.review_conversations_task',
            'schedule': 3600.0,
        },
    },
)
