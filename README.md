# SwiftAnswer

SwiftAnswer is a multi-tenant, Retrieval-Augmented Generation (RAG) platform. Users create isolated knowledge bases by uploading documents or crawling websites. An AI chat interface then answers natural-language questions grounded in those sources. Each tenant is fully isolated, and access is gated by Supabase Auth with a prepaid CHF credit billing system powered by Stripe.

**Tech Stack:** Vue 3 · Flask · Celery · Redis · ChromaDB · Supabase · Stripe · Docker Compose

---

## Features

| Area | Details |
|---|---|
| **Knowledge ingestion** | Upload PDFs, DOCX, TXT, CSV **or** provide a URL for full recursive site crawls via Playwright/Crawl4AI |
| **RAG chat** | Per-tenant vector store (ChromaDB) with Gemini models for embedding and answer generation |
| **Multi-tenancy** | Each user manages isolated tenants; tenant is addressed by UUID in the URL |
| **Embeddable widget** | `/api/tenants/:id/widget` endpoint serves a self-contained chat widget for third-party embedding |
| **Authentication** | Supabase Auth (email/password); Flask routes protected by a `@token_required` JWT decorator |
| **Billing** | Prepaid CHF balance via Stripe Checkout; one-time top-up or recurring monthly subscription; Stripe Customer Portal for self-serve management |
| **Usage tracking** | Per-user token and cost aggregation across chat and indexing jobs, exposed in the dashboard |
| **Analytics** | Chat log viewer with per-tenant session history |
| **i18n** | Vue i18n with locale files under `frontend/src/locales/` |
| **Background jobs** | Celery workers handle all long-running tasks (crawls, file processing, chat streaming) |
| **Job scheduler** | Celery Beat runs a `job_scheduler_task` every 30 s for recurring maintenance |

---

## Architecture

```
┌─────────────┐     HTTP      ┌──────────────────┐     tasks      ┌─────────────────┐
│  Vue 3 SPA  │ ────────────▶ │   Flask API       │ ─────────────▶ │  Celery Worker  │
│  (port 5173)│               │   (port 5000)     │               │  (concurrency=12│
└─────────────┘               └──────────────────┘               │  in prod)       │
                                       │                          └────────┬────────┘
                               ┌───────┴────────┐                         │
                               │   Supabase     │                  ┌──────▼───────┐
                               │  (auth + DB)   │                  │    Redis     │
                               └────────────────┘                  │  (broker +   │
                                                                    │   results)   │
                                                                    └──────────────┘
```

**Flask blueprints:**

| Blueprint | Prefix | Responsibilities |
|---|---|---|
| `auth_bp` | `/api/auth` | Login, signup, token validation |
| `tenants_bp` | `/api/tenants` | Tenant CRUD |
| `sources_bp` | `/api/tenants` | File upload, URL crawl, link discovery |
| `widget_bp` | `/api/tenants` | Public embeddable widget endpoint |
| `chat_bp` | `/api/chat` | Streaming RAG chat |
| `billing_bp` | `/api/billing` | Balance, usage, Stripe checkout, portal, webhooks |

**Celery tasks:**

| Task | File | Trigger |
|---|---|---|
| `chat_task` | `app/chat/tasks.py` | `POST /api/chat` |
| `process_local_filepath` | `app/data_processing/tasks.py` | File upload route |
| `process_urls` | `app/data_processing/tasks.py` | URL crawl route |
| `crawl_links_task` | `app/data_processing/tasks.py` | Link discovery route |
| `job_scheduler_task` | `app/data_processing/tasks.py` | Celery Beat every 30 s |

---

## Local Development

### Prerequisites

- Docker & Docker Compose

### 1. Configure Environment Variables

Copy `.env` (already present in the repo) and ensure the following keys are set:

```env
# Supabase
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_KEY=<your-service-key>

# Google Gemini
GOOGLE_API_KEY=<your-google-api-key>

# Flask
SECRET_KEY=<random-hex-string>   # python -c "import secrets; print(secrets.token_hex(32))"

# Models (optional — defaults shown)
CHAT_GEMINI_MODEL=gemini-3.1-flash-lite-preview
INDEXING_GEMINI_MODEL=gemini-3.1-pro-preview

# Stripe (use test keys locally)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:5173
```

> `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, Redis URLs, and data-path variables are pre-configured for local Docker use and do not need to be changed.

### 2. Start the Stack

```sh
docker compose up --build
```

> ⚠️ The first build downloads Playwright/Chromium browsers for web crawling and can take several minutes.

### Accessing the Application

| Service | URL |
|---|---|
| Frontend dashboard | http://localhost:5173 (hot-reload) |
| Backend API | http://localhost:5000 (hot-reload) |
| Health check | http://localhost:5000/api/health |

### Stopping

```sh
docker compose down
```

---

## Production Deployment

Production uses `docker-compose.prod.yml`, which differs from the dev config in the following ways:

- **Backend** runs under Gunicorn (8 workers, 120 s timeout)
- **Celery worker** runs with `--concurrency=12`
- **Frontend** is built as a static bundle served by Nginx
- **Nginx** terminates TLS and reverse-proxies to the backend and frontend containers
- All services have `restart: always`

### Deploying

Run the one-shot deploy script from your local machine:

```sh
./deploy.sh
```

This script:
1. `rsync`s the repo to the server at `root@142.132.206.182:/var/www/burncodes-ai`
2. Installs Docker on the server if not present
3. Provisions a Let's Encrypt TLS certificate for `ai.burn.codes` via Certbot if one doesn't exist
4. Runs `docker compose -f docker-compose.prod.yml build && up -d --force-recreate`

### Useful Commands on the Server

```sh
# View logs for all services
./logs.sh

# Rebuild and restart
docker compose -f docker-compose.prod.yml build && docker compose -f docker-compose.prod.yml up -d --force-recreate
```

---

## Frontend Views

| View | Route | Description |
|---|---|---|
| `Login.vue` | `/login` | Supabase email/password login |
| `Signup.vue` | `/signup` | New user registration |
| `Tenant.vue` | `/tenant/:id` | Per-tenant dashboard (sources + chat) |
| `Chat.vue` | `/chat/:tenantId` | Full-page chat interface |
| `ChatLogs.vue` | `/logs` | Historical chat session viewer |
| `Subscription.vue` | `/billing` | Balance, top-up, usage stats, billing history |
| `Analytics.vue` | `/analytics` | Usage analytics across tenants |
| `Profile.vue` | `/profile` | Account settings |
| `ManageTenants.vue` | `/tenants` | Create / manage tenants |

---

## Known Issues & Technical Debt

See [`tasks.md`](./tasks.md) for the full backlog. Key items:

- **Zombie PROCESSING states** — if a container restarts mid-crawl, the source row is permanently stuck in `PROCESSING`. A Celery Beat reconciliation cron ("Zombie Reaper") is planned.
- **Celery Late ACKs** — already configured (`task_acks_late=True`, `worker_prefetch_multiplier=1`) so tasks are requeued on worker crash, but idempotency of crawl tasks still needs hardening.
- **Headless browser concurrency** — jitter delays and `shm_size: 2gb` are in place; queue separation (Playwright-heavy vs. fast text tasks) is a planned improvement.
