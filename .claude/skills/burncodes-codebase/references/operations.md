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

### Normal way: a release tag

Everything reaches production as a version tag on `main`:

1. Work on a branch, push it, merge it into `main` through a PR (CI must be green).
2. Run new SQL from `supabase/migrations/` in the Supabase SQL editor **before**
   tagging; deploys never migrate.
3. Tag the merged `main` and push the tag:
   ```sh
   git checkout main && git pull
   git tag v1.2.3 && git push origin v1.2.3
   ```
4. `.github/workflows/release.yml` runs: the CI checks, a check that the tag
   is on `main`, `./_prod_deploy.sh` with the deploy key, a wait (up to 5 min)
   for `https://ai.burn.codes/api/health`, then a GitHub release with notes.
   Follow it under GitHub → Actions → Release; a failed check stops it before
   anything reaches the server.

Versions: patch (`v1.2.4`) for fixes, minor (`v1.3.0`) for features, major for
breaking changes. Never move or reuse a tag: a broken release is fixed by the
next one.

Setup (done 2026-10-31): GitHub environment **`Prod`** (GitHub can't rename
environments, so the workflow uses this name) with the **secret**
`PROD_SSH_KEY` (private key of `github-deploy burncodes-ai`, stored on the
user's machine as `~/.ssh/burncodes_deploy`) and the **variable**
`PROD_KNOWN_HOSTS` (the server's public ed25519 host key); optionally the
variable `PROD_SERVER` (default `root@142.132.206.182`). The deploy key is in
the server's `authorized_keys` with `no-pty,no-port-forwarding,…`.

The workflow deploys a clean checkout, without `.env`: **the server's
`/var/www/burncodes-ai/.env` is the production configuration**; change
settings there and restart the affected containers.

### Pushing and server access from a Claude session

- The user's default key (`~/.ssh/id_ed25519`) has a passphrase; **don't
  change the user's default key or SSH/git config**.
- `~/.ssh/id_ed25519_new` (no passphrase) is on GitHub and on the server for
  sessions to use, explicitly per command:
  ```sh
  GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_new -o IdentitiesOnly=yes -o BatchMode=yes" git push origin <branch>
  ssh -i ~/.ssh/id_ed25519_new -o IdentitiesOnly=yes -o BatchMode=yes root@142.132.206.182 '<read-only command>'
  ```
- Read-only checks on the server are fine. Changes on the server (files,
  `authorized_keys`, `.env`, restarting containers) need the user's explicit
  go-ahead each time; otherwise give them the command.
- Pushing a release tag deploys to production: only when the user asks for it.
- `gh` isn't installed: create PRs through the `pull/new/<branch>` link or the
  GitHub web UI (Chrome).

### Fallback: deploying from the machine

`./_prod_deploy.sh` (repo root) still works for emergencies: rsync the
**working tree** (uncommitted changes go live!) to
`root@142.132.206.182:/var/www/burncodes-ai`, then on the server: `build`
with the layer cache, `up -d` (recreates only containers whose image or
settings changed; no `down`, queues are kept), `restart nginx`, prune old images.
The release workflow runs the same script.

Why it's fast: every Dockerfile installs dependencies before copying code, so a
code change rebuilds only the last layers; pip/npm/Chromium are reinstalled
only when `requirements.txt` / `package-lock.json` change. Don't add
`--no-cache` or `down` back: `--no-cache` re-downloads Chromium (~minutes), `down`
stops everything and threw away queued tasks. nginx must restart after every
deploy: it resolves `backend`/`frontend` to IPs at start (recreated containers
get new ones → 502) and reads `nginx/nginx.conf` only at start.
It also copies the local `.env` to the server (rsync excludes only `.env.*`),
overwriting the production configuration with the local one: prefer a tag.
`./_prod_frontend_deploy.sh` rebuilds the frontend only.

### After a deploy

- `curl -fsS https://ai.burn.codes/api/health`
- A new frontend string is in the live bundle (`/assets/index-*.js` and chunks).
- A new backend module loads: if chat stops answering ("Ich suche das Passende
  für dich …" forever), suspect a missing `COPY` in a worker Dockerfile first.
- Test a chatbot on `https://ai.burn.codes/chat/<tenant-id>` (younity:
  `d4d5099f-5e51-4710-b2e9-3a7c25f6cfac`).

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
