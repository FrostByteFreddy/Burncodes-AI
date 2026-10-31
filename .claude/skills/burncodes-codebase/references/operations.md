# Operations

## Local stack

```sh
docker compose -p swiftanswer-local up --build -d \
  redis backend celery_worker_fast celery_worker_heavy celery_worker_chat frontend
```

- No `celery_beat`: the local `.env` uses the production Supabase project.
- Frontend http://localhost:5173 hot-reloads (source mounted). It runs
  `npm install` at every start, which may rewrite `frontend/package-lock.json`:
  don't commit that by accident. Backend
  containers don't: rebuild, or for a quick check
  `docker cp <file> swiftanswer-local-<service>-1:/app/app/<path>` (the image
  layout is `/app/app/` = the service's `app/` with `shared/` copied in).
- Container names: `swiftanswer-local-{backend,celery_worker_fast,celery_worker_heavy,celery_worker_chat,frontend,redis}-1`.
- Run code against the real data from a container, e.g.
  `docker exec -i swiftanswer-local-backend-1 python - <<'EOF' … EOF`
  (`from app.database.supabase_client import supabase, fetch_all`).

## Tests

```sh
cd backend && pip install -r services/api/requirements.txt -r requirements-test.txt && python -m pytest
```

Without a local Python setup, in the backend image with the repo mounted:

```sh
cd backend && docker run --rm -v "$PWD":/src -w /src --entrypoint sh \
  $(docker inspect swiftanswer-local-backend-1 --format '{{.Config.Image}}') \
  -c "pip install -q -r requirements-test.txt >/dev/null; python -m pytest -q -p no:cacheprovider"
```

There `test_task_names` fails for setup reasons (it reads worker files from
the repo root, which only `backend/` is mounted as); with the whole repo, as
in CI, all tests pass. CI also runs `npm audit --audit-level=high`: check it
locally with `npm audit --audit-level=high` in `frontend/` after dependency changes.

Frontend: `docker exec swiftanswer-local-frontend-1 sh -c "cd /app && npx vite build --outDir /tmp/b"`.

Before trusting a new backend module, build the affected image as production
does, e.g. `docker build -f services/worker_chat/Dockerfile -t check backend/`
and import the code inside it.

## Deploy

`./_prod_deploy.sh` (from the repo root): rsync the working tree to
`root@142.132.206.182:/var/www/burncodes-ai`, rebuild, flush the Celery
queues, `up -d --scale celery_worker_heavy=$DEPLOY_HEAVY_WORKERS` (10).
Uncommitted changes go live; migrations don't (Supabase SQL editor first).
`./_prod_frontend_deploy.sh` for frontend only. Releases via version tags on
`main` run `.github/workflows/release.yml`.

Sessions can't SSH to the server or push to GitHub without the user's key
agent: give the user the command to run.

## Checking production

```sh
docker stats --no-stream                                    # CPU / RAM
free -h; uptime
docker compose -f docker-compose.prod.yml exec redis sh -c \
  'for q in heavy fast chat; do echo "$q: $(redis-cli llen $q)"; done'   # waiting tasks
docker compose -f docker-compose.prod.yml exec redis sh -c \
  'for k in $(redis-cli --scan --pattern "crawl:interval:*"); do echo "$k $(redis-cli get $k) ms"; done'
```

Many waiting `heavy` tasks with idle CPU = the per-site pace, not capacity
(`crawl:interval:<host>` up to 10000 ms; `redis-cli del` resets it).

From the logged-in dashboard in Chrome, the live bundle can be checked for a
change by searching `/assets/index-*.js` and its chunks for a new string.

Data checks (via a local container, production DB):
- runs/sources of a chatbot: `crawling_jobs`, `tenant_sources` by `tenant_id`
- orphaned Gemini documents: list the store's documents and compare with the
  rows' `gemini_document_names`
- ledger consistency: sum of `billing_ledger.amount_chf` per user = `user_billing.balance_chf`
