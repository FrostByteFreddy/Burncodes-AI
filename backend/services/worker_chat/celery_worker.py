"""
services/worker_chat/celery_worker.py
Registers ONLY the chat queue task: LLM RAG inference.
No crawl4ai, no Flask, no file ingestion.
"""
import nest_asyncio
nest_asyncio.apply()

import os
from celery import Celery
from dotenv import load_dotenv
from app.logging_config import error_logger

load_dotenv()

celery = Celery('worker_chat')
celery.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue='chat',
)

# Explicitly import to register @shared_task decorators
import app.chat.tasks  # noqa: F401, E402

error_logger.info("worker_chat: tasks registered — chat queue ready")
