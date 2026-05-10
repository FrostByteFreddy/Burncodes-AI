"""
worker_heavy/app/data_processing/ingestion/file_ingester.py

SUPERSEDED — file ingestion is now handled by process_file_url in worker_fast.
Worker_heavy crawl_tasks.py dispatches FILE_URL sources via Celery to worker_fast.
This stub exists to prevent import errors from any legacy code paths.
"""
