# SwiftAnswer Future Tasks & Technical Debt

## 1. Deployment Reliability & Data Integrity
Currently, if a backend deploy occurs (e.g. `docker compose up --build`) while a user is actively running a URL crawl, the process will be abruptly killed. This causes the UI to be permanently stuck in the `PROCESSING` state because the script never reaches the Supabase completion/failure step.

### Proposed Solutions:
- [x] **Implement Celery Late ACKs (`acks_late = True`)**  
  Configure the Celery worker to only acknowledge a task as completed *after* it successfully runs. This way, if a container is abruptly restarted, the dropped task remains in the Redis queue and is gracefully retried upon startup.  
  ✅ Implemented in `app/__init__.py` — `task_acks_late=True` and `worker_prefetch_multiplier=1`.

- [x] **State Reconciliation Cron Job ("Zombie Reaper")**  
  ✅ Implemented as `zombie_reaper_task` in `app/data_processing/tasks.py`. Runs every 30 min via Celery Beat. Finds `tenant_sources` rows stuck in `PROCESSING` for > 4 h and marks them `ERROR`.

- [x] **Increase Docker Grace Period**  
  ✅ Added `stop_grace_period: 60s` to `celery_worker` in both `docker-compose.yml` and `docker-compose.prod.yml`. Also fixed missing `shm_size: '2gb'` in the prod compose.

## 2. Headless Browser Concurrency Tuning
During deep crawls, large queues can instantly trigger the initialization of numerous headless Browsers via `Playwright/Crawl4AI`. 

### Progress:
- [x] **Jitter Applied:** Random staggered sleeps (`0.5s - 5.0s`) were introduced before browser launches to prevent immediate unified CPU lockup upon enqueue.
- [x] **IPC Shared Memory Increased:** Set `shm_size: '2gb'` to prevent shared memory limits from crashing the Chromium driver.

### Proposed Solutions:
- [x] **Queue Separation**  
  ✅ All tasks now carry an explicit `queue=` parameter. `process_single_url_task` is routed to `heavy`; everything else (chat, file processing, orchestrators, Beat jobs) goes to `fast`. Both compose files now run two separate worker containers:
  - `celery_worker_fast` — concurrency 8 (dev) / 10 (prod), no shm needed
  - `celery_worker_heavy` — concurrency 2, `shm_size: 2gb`, `stop_grace_period: 60s`
  Celery config also sets `task_default_queue='fast'` and `task_routes` as a belt-and-suspenders fallback.

## 3. Vector DB Deletion
- [x] **Delete from vector DB on source removal**  
  ✅ Fixed in commit `2dee0a4` — `sources.py` now calls `db._collection.delete(where={"source_id": source_id})` when a source is deleted, ensuring ChromaDB chunks are removed alongside the Supabase row.