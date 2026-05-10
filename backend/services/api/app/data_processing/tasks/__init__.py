"""
api/app/data_processing/tasks/__init__.py
Thin task stubs for the API service.

The API only *dispatches* tasks — it never executes them.
We use celery.signature() so the API can call .delay() without importing
the actual worker code (chromadb, langchain, crawl4ai).
"""
from app import celery

def _task(name, queue='fast'):
    """Return a task proxy that can be .delay()ed from the API."""
    return celery.signature(name, queue=queue)

# --- Task references used by sources.py / tenants routes ---
# These names MUST exactly match the @shared_task function names in workers.

class _TaskProxy:
    """Minimal proxy exposing .delay() for a named Celery task."""
    def __init__(self, task_name, queue='fast'):
        self._name = task_name
        self._queue = queue

    def delay(self, *args, **kwargs):
        return celery.send_task(self._name, args=args, kwargs=kwargs, queue=self._queue)


# Task names = module_path.function_name as registered by @shared_task in each worker
process_local_file = _TaskProxy('app.data_processing.tasks.process_local_file', queue='fast')
process_urls       = _TaskProxy('app.data_processing.tasks.process_urls',        queue='fast')
process_file_url   = _TaskProxy('app.data_processing.tasks.process_file_url',    queue='fast')
crawl_links_task   = _TaskProxy('app.data_processing.tasks.crawl_tasks.crawl_links_task', queue='heavy')
