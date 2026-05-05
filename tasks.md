# SwiftAnswer Future Tasks & Technical Debt

## 1. Deployment Reliability & Data Integrity
Currently, if a backend deploy occurs (e.g. `docker compose up --build`) while a user is actively running a URL crawl, the process will be abruptly killed. This causes the UI to be permanently stuck in the `PROCESSING` state because the script never reaches the Supabase completion/failure step.

### Proposed Solutions:
- [x] **Implement Celery Late ACKs (`acks_late = True`)**  
  Configure the Celery worker to only acknowledge a task as completed *after* it successfully runs. This way, if a container is abruptly restarted, the dropped task remains in the Redis queue and is gracefully retried upon startup.  
  ✅ Implemented in `app/__init__.py` — `task_acks_late=True` and `worker_prefetch_multiplier=1`.

- [ ] **State Reconciliation Cron Job ("Zombie Reaper")**  
  Since things inevitably crash, create a scheduled cleanup task (e.g., using Celery Beat) that queries `tenant_sources` for any row where `status = 'PROCESSING'` but the `created_at` timestamp is older than 2–6 hours. Automatically revert these to `ERROR` or resubmit them to `PENDING` to keep the UI in sync.

- [ ] **Increase Docker Grace Period**  
  Update `docker-compose.yml` with `stop_grace_period: 60s` for the `celery_worker` to give running Playwright instances more time to successfully wrap up logging and state-saves before the final SIGKILL is dispatched.

## 2. Headless Browser Concurrency Tuning
During deep crawls, large queues can instantly trigger the initialization of numerous headless Browsers via `Playwright/Crawl4AI`. 

### Progress:
- [x] **Jitter Applied:** Random staggered sleeps (`0.5s - 5.0s`) were introduced before browser launches to prevent immediate unified CPU lockup upon enqueue.
- [x] **IPC Shared Memory Increased:** Set `shm_size: '2gb'` to prevent shared memory limits from crashing the Chromium driver.

### Proposed Solutions:
- [ ] **Queue Separation**  
  Separate fast tasks (text extraction, splitting) from heavy tasks (Playwright headless Chromium). Limit the heavy queue to `--concurrency=2` while allowing the fast queue to aggressively consume available cores.

## 3. Vector DB Deletion
- [x] **Delete from vector DB on source removal**  
  ✅ Fixed in commit `2dee0a4` — `sources.py` now calls `db._collection.delete(where={"source_id": source_id})` when a source is deleted, ensuring ChromaDB chunks are removed alongside the Supabase row.