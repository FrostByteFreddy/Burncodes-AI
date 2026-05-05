# Workers — instant, no rebuild
docker compose restart celery_worker_heavy celery_worker_fast

# Backend API — instant
docker compose restart backend

# Everything
docker compose restart backend celery_worker_heavy celery_worker_fast celery_beat