# Backend

`backend/` holds five services and the code they share. Each service has its own
`Dockerfile` and `requirements.txt`; the build context is `backend/`.

| Service | Folder | Queue | Runs |
|---|---|---|---|
| api | `services/api` | — | Flask under gunicorn (8 workers × 16 threads, 120 s timeout) |
| worker_heavy | `services/worker_heavy` | `heavy` | crawling, `--concurrency=1` per container, 10 containers in production (each a Chromium) |
| worker_fast | `services/worker_fast` | `fast` | learning, uploads, scheduler, re-crawls, reviews; `--concurrency=8` |
| worker_chat | `services/worker_chat` | `chat` | answers; `--concurrency=4` |
| beat | `services/beat` | — | Celery beat: triggers the periodic tasks |

## Shared code (`backend/shared/`)

Symlinked into `services/*/app/` (relative links, tracked by git), copied by the
Dockerfiles. Edit the files in `shared/`, never through a service's link.
api, worker_fast and worker_heavy copy `shared/knowledge/` whole; **worker_chat
copies single files** (see SKILL.md rule 1).

| Module | Does |
|---|---|
| `ai_models.py` | every model and price setting from `.env`; `learning_rates()`, `billable_tokens()`, `count_tokens()` |
| `auth/` | `token_required` / `optional_user` decorators; change password; delete account |
| `billing/services.py` | `BillingService`: balance, `charge()` (ledger), Stripe checkout and crediting |
| `database/` | Supabase service-role client, `fetch_all()` (pages through PostgREST's 1000-row cap), `retrying_execute()` |
| `gemini_store/service.py` | File Search stores and documents: `get_or_create_store`, `upload_text`, `delete_document`, `delete_store` |
| `logging_config.py` | `error_logger`; files under `/app/data/logs` |
| `models/` | enums: `CrawlingStatus`, `SourceType` |
| `security/url_guard.py` | `is_public_url`, `safe_client`: every fetch of a user-given URL goes through it (no private IPs, also on redirects) |
| `soup_extractor.py` | light HTML fetch + link extraction ("soup" crawl mode); copied into worker_heavy and worker_fast, not the API |
| `knowledge/` | the knowledge pipeline, see `knowledge-pipeline.md` |

## API (`services/api/app/`)

Blueprints, registered in `__init__.py`. "auth" = `@token_required` and the
route checks the chatbot belongs to the user (`.eq('user_id', current_user.id)`).
`tests/test_security.py` fails if a new route is neither marked public nor protected.

| Prefix | File | Routes |
|---|---|---|
| `/api/auth` | `shared/auth/routes.py` | `POST change-password`, `DELETE account` |
| `/api/tenants` | `tenants/routes.py` | chatbot CRUD; `GET /<id>/public` (widget config, public); `GET /<id>/overview` (dashboard figures, spend from the ledger); `insights/findings` (+ `PATCH`), `POST insights/review`; `POST branding` (colours/logo from the website, 10/min) |
| `/api/tenants` | `tenants/sources.py` | `GET sources`, `POST sources/upload`, `POST sources/crawl` (single pages), `POST sources/discover` (start a crawl); `crawling_jobs` list/get/`progress`/`log`; `confirm` (pay + learn, body `{"model"}`), `skipped`, `selection` (GET/POST: leave out folders), `resume`, `cancel`; `DELETE crawling_jobs/<id>` (in rounds, 202 = not done yet), `DELETE sources/<id>`, `DELETE sources` (everything); `knowledge/overview`; `store-stats` |
| `/api/tenants` | `tenants/widget.py` | `GET widget.js` (public) |
| `/api/calendar` | `tenants/calendar_feed.py` | `GET /<tenant>` feeds, `GET /<tenant>/<keys>.ics` (public; only active, unprotected bots with `calendar_feeds`) |
| `/api/chat` | `chat/routes.py` | `POST /<tenant>` (public, rate-limited, owner's balance must be > 0) → task id; `GET task/<id>/status` (long poll ≤ 30 s); `intro`, `unlock` (test-page password), share links; owner-only `analytics`, `conversations`, `conversation/<id>` |
| `/api/billing` | `billing/routes.py`, `webhooks.py` | `balance`, `usage` (from the ledger), `history`, `create-checkout-session`, `portal`, `verify-session`, `webhook` (Stripe, public, signature-checked) |
| `/api/health` | `__init__.py` | health check |

Password-protected test pages: `chat/access.py` (hash, signed unlock token).
Chat abuse limits: `chat/guard.py` (`CHAT_LIMIT_PER_IP`, per tenant, long-poll slots).

## Celery tasks

Task names are full dotted paths; the API and other workers send them by name
(`jobs.LEARN_TASK`, `SCAN_TASK`, …). `tests/test_task_names.py` checks the names
used match the registered ones.

| Task | Worker | Started by |
|---|---|---|
| `crawl_links_task` | heavy | `POST sources/discover`, `sources/crawl`, weekly re-crawl: creates the job, queues the start page |
| `process_single_url_task` | heavy | each discovered page/file (scan: fetch, fingerprint, record) |
| `start_learning_task` | fast | `confirm` → `jobs.start_learning` |
| `learn_source_task` | fast | one per source to learn → `learn.learn_source` |
| `process_local_file` | fast | upload → learns the file right away |
| `job_scheduler_task` | fast | beat, every 30 s: re-sends lost tasks, finishes jobs |
| `zombie_reaper_task` | fast | beat: sources stuck in PROCESSING > 1 h → ERROR |
| `weekly_recrawl_task` | fast | beat: re-crawls runs older than the chatbot's interval (one per chatbot per run) |
| `review_conversations_task` | fast | beat nightly, or `POST insights/review` |
| `chat_task` | chat | `POST /api/chat/<tenant>` |
