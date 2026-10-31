# Burncodes AI

Chatbots that know an organisation's website. A customer (a Swiss municipality,
a course platform, a club) enters their website; Burncodes AI reads it, shows
what learning it will cost, and after payment learns every page and document.
The chatbot then answers visitors on the customer's site, as an embedded
widget or a shareable test page, with links to its sources, verified dates
(waste collection, events) and facts (fees, opening hours).

Live at **https://ai.burn.codes**.

**Stack:** Vue 3 · Tailwind · Flask · Celery · Redis · Supabase (Postgres, Auth, Realtime) · Google Gemini (File Search) · Stripe · Docker Compose · nginx

---

## What it does

| Area | What happens |
|---|---|
| **Reading a website** (free) | A crawl starts at an address and follows links within the site (Playwright, or a light "soup" mode), optionally reads the sitemap, keeps to one language and skips sign-up pages. Every page and document is fingerprinted, so unchanged ones cost nothing later. |
| **Estimate → payment → learning** | After reading, an AI step sorts out what isn't worth learning (old minutes, outdated versions). The customer sees the estimated cost per learning model (lite / argon), can leave out folders, and confirms; learning only starts when the prepaid balance covers it. |
| **Learning** | Gemini reads each new or changed page/file once: sections for search (Gemini File Search, one store per chatbot), plus facts and dates stored in our database. Calendar dates from PDFs are cross-checked against the PDF's grid. |
| **Answers** | The chat model gets the visitor's date and time, the dates and facts relevant to the question, the contact card from the website footer, and searches the chatbot's store. Misspelled names are recognised. Answers carry source links and "add to calendar" buttons. |
| **Keeping up to date** | Scheduled re-crawls (per chatbot, every N days) learn only what changed, approved automatically up to a cost cap. Pages removed from the site disappear after two crawls. |
| **Insights** | Questions per day, conversations, and a nightly review that lists questions the bot couldn't answer or got pushback on. |
| **Billing** | Prepaid CHF balance via Stripe (one-time or monthly). Every top-up and every charge (answer, learning, review) is a row in a ledger. |
| **Widget** | `<script src="https://ai.burn.codes/api/tenants/widget.js" data-tenant-id="…">` adds a launcher; colours, logo and name can be taken from the customer's website. |
| **Languages** | Dashboard in German (Swiss spelling), English and French. The bot answers in the visitor's language. |

---

## Architecture

```
 customer website ── widget.js ──▶ iframe /chat/:tenantId?widget
                                          │
 ┌──────────────┐  /api/  ┌───────────────▼───────────────┐
 │ nginx (TLS)  │────────▶│ api: Flask + gunicorn (8×16)  │◀── Stripe webhooks
 │              │  /      │ frontend: Vue SPA (static)    │
 └──────────────┘────────▶└───────┬───────────────┬───────┘
                                  │               │ Celery tasks (Redis broker)
             Supabase ◀───────────┤               ▼
     (Postgres, Auth, Realtime)   │   ┌──────────────┬───────────────┬─────────────┐
             ▲ live progress      │   │ worker_heavy │ worker_fast   │ worker_chat │ celery_beat
             └──── dashboard      │   │ ×10, crawl   │ learn, review │ answers     │ schedules
                                  │   └──────┬───────┴───────┬───────┴──────┬──────┘
                                  └──────────┴──── Gemini (File Search, models) ──┘
```

| Service | Code | Does |
|---|---|---|
| `backend` (api) | `backend/services/api` | REST API for dashboard, widget and Stripe |
| `celery_worker_heavy` | `backend/services/worker_heavy` | Reads websites (Playwright/Chromium), one page per task; 10 containers in production |
| `celery_worker_fast` | `backend/services/worker_fast` | Learns sources, uploads, the watchdog scheduler, re-crawls, conversation reviews |
| `celery_worker_chat` | `backend/services/worker_chat` | Answers chat messages |
| `celery_beat` | `backend/services/beat` | Triggers the periodic tasks |
| `frontend` | `frontend/` | Dashboard, chat page, widget iframe |

Code used by several services lives in `backend/shared/` (knowledge pipeline,
Gemini store, billing, auth, database client, AI model settings, URL guard). It
is symlinked into each service's `app/` for development and copied into the
images by the Dockerfiles. **The chat worker's Dockerfile copies knowledge
modules one by one**: a new module it imports must be added there
(`backend/tests/test_images.py` checks this).

More detail (where what is, how the pipeline works, pitfalls):
`.claude/skills/burncodes-codebase/`.

---

## Local development

### 1. Environment

Create `.env` in the repository root:

```env
# Supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service-role key>
SUPABASE_ANON_KEY=<anon key>
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon key>

# Google Gemini
GOOGLE_API_KEY=<key>

# Flask
SECRET_KEY=<random hex>          # python -c "import secrets; print(secrets.token_hex(32))"
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173

# Stripe (test keys locally)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

All other settings have defaults; see [Configuration](#configuration).

Apply the database schema in `supabase/migrations/` (Supabase SQL editor or `supabase db push`).

### 2. Start the stack

```sh
docker compose -p swiftanswer-local up --build -d \
  redis backend celery_worker_fast celery_worker_heavy celery_worker_chat frontend
```

- **Leave out `celery_beat` when your `.env` points at the production database**:
  otherwise scheduled re-crawls and reviews run twice (locally and on the server).
- The frontend (http://localhost:5173) reloads on changes. **The backend
  containers don't**: their code is baked into the image, so rebuild after
  backend changes (`docker compose -p swiftanswer-local up --build -d backend celery_worker_chat`, …).
- API: http://localhost:5000, health check: http://localhost:5000/api/health.
- The first build downloads Chromium for the crawler and takes several minutes.

### 3. Tests

```sh
cd backend
pip install -r services/api/requirements.txt -r requirements-test.txt
python -m pytest
```

CI (`.github/workflows/ci.yml`) runs the backend tests, a compile check, the
frontend build and `npm audit --audit-level=high` on every PR.

---

## Production

`docker-compose.prod.yml` on the server (`/var/www/burncodes-ai`): nginx
terminates TLS and proxies `/api/` to the API, everything else to the static
frontend; `/chat/` may be framed by any site (the widget).

| Script | Does |
|---|---|
| `./_prod_deploy.sh` | rsyncs the **working tree** (uncommitted changes included) to the server, builds and restarts everything, starts `DEPLOY_HEAVY_WORKERS` crawl workers (default 10) |
| `./_prod_frontend_deploy.sh` | rebuilds and restarts the frontend only |
| `./_prod_logs.sh` | tails the logs on the server |
| `./_restart_docker.sh` | restarts the stack |

**Database changes are not deployed by the scripts.** Run new migrations in the
Supabase SQL editor before deploying code that needs them.

Useful on the server:

```sh
docker stats --no-stream                                   # CPU / RAM per container
docker compose -f docker-compose.prod.yml exec redis sh -c \
  'for q in heavy fast chat; do echo "$q: $(redis-cli llen $q)"; done'   # waiting tasks
docker compose -f docker-compose.prod.yml exec redis redis-cli \
  --scan --pattern 'crawl:interval:*'                      # websites currently slowed down
```

### Releasing

Pushing a version tag from `main` (`git tag v1.5.0 && git push origin v1.5.0`)
runs `.github/workflows/release.yml`: CI checks, deploy with `_prod_deploy.sh`,
wait for `/api/health`, GitHub release. It needs the GitHub environment `Prod`
with the **secret** `PROD_SSH_KEY` (private key of `github-deploy burncodes-ai`,
in the server's `authorized_keys`) and the **variable** `PROD_KNOWN_HOSTS`
(`ssh-keyscan -t ed25519 142.132.206.182`); optionally the variable `PROD_SERVER`.
The GitHub deploy has no `.env`: the server keeps its own, change settings there.

---

## Configuration

Read from `.env` at container start (restart after changing). Defaults in brackets.

| Setting | Meaning |
|---|---|
| `CHAT_GEMINI_MODEL` [`gemini-3.1-flash-lite`] | answers chat messages; fast models only, answers should take ~5 s |
| `CHAT_THINKING_LEVEL` [model default] | `low`/`medium`/`high`; thinking is billed and slow |
| `CHAT_HISTORY_TURNS` [10] | earlier exchanges sent with a question |
| `INDEXING_GEMINI_MODEL` [`gemini-4-argon`] | default for reading documents |
| `LEARNING_LITE_MODEL` / `LEARNING_ARGON_MODEL` | the two learning models customers choose between |
| `TRIAGE_GEMINI_MODEL`, `REVIEW_GEMINI_MODEL` [`gemini-3.1-flash-lite`] | sorting pages before the estimate; reviewing conversations |
| `EMBEDDING_GEMINI_MODEL` [`gemini-embedding-2`] | only for File Search stores created from now on |
| `LEARNING_PRICE_FACTOR` [5] · `USD_TO_CHF` [0.80] | learning price = Google's list price × factor, in CHF |
| `CHAT_RATE_CHF_PER_1M_INPUT/OUTPUT` [8 / 17.5] | what an answer costs the customer |
| `REVIEW_RATE_CHF_PER_1M_INPUT/OUTPUT` [8 / 17.5] | what a conversation review costs |
| `RECRAWL_AUTO_CONFIRM_MAX_CHF` [5] | scheduled re-crawls start learning by themselves up to this estimate |
| `INDEXING_MAX_PAGES` [20] | longer PDFs are made searchable only (no facts/dates) |
| `CRAWL_HOST_INTERVAL_MS` [1000] | pause between two requests to the same website |
| `CHAT_LIMIT_PER_IP` / `CHAT_LIMIT_PER_TENANT` | chat rate limits |
| `APP_TIMEZONE` [`Europe/Zurich`] | "today" for dates in answers |

---

## Repository map

```
backend/
  services/api/            Flask app: auth, tenants (chatbots), sources, chat, billing, widget, calendar feeds
  services/worker_*/       Celery workers (see Architecture)
  shared/                  code used by several services
    knowledge/             the knowledge pipeline: crawl scope, learning, dates, facts, names, review …
    gemini_store/          File Search stores and documents
    billing/services.py    balance, charges, Stripe crediting
    ai_models.py           every model and price setting
  tests/                   pytest
frontend/src/
  views/                   pages (Overview, Insights, Onboarding, account settings, chat …)
  components/tenant/       knowledge, crawl detail, chatbot appearance
  components/ui/           design system components (Bc*)
  assets/tokens.css        design tokens; bc.css components; legacy.css bridge for older screens
  locales/                 de / en / fr
supabase/migrations/       database schema (one idempotent file)
docs/design/               design brief the design system was made from
nginx/                     production proxy config
```
