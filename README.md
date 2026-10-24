# SwiftAnswer

SwiftAnswer is a multi-tenant, Retrieval-Augmented Generation (RAG) platform. Users create isolated knowledge bases by uploading documents or crawling websites. An AI chat interface then answers natural-language questions grounded in those sources. Each tenant is fully isolated, and access is gated by Supabase Auth with a prepaid CHF credit billing system powered by Stripe.

**Tech Stack:** Vue 3 · Flask · Celery · Redis · Gemini File Search · Supabase · Stripe · Docker Compose

---

## Features

| Area | Details |
|---|---|
| **Knowledge ingestion** | Upload PDFs, DOCX, TXT, images **or** crawl a website (Playwright via Crawl4AI, or a lightweight httpx/trafilatura "soup" mode) |
| **RAG chat** | One Gemini File Search store per tenant; Gemini handles chunking, embedding and retrieval, and answers with citations |
| **Multi-tenancy** | Each user manages isolated tenants; tenant is addressed by UUID in the URL |
| **Embeddable widget** | `/api/tenants/widget.js` injects a launcher + iframe (`/chat/:tenantId?widget`) into any site |
| **Authentication** | Supabase Auth in the frontend (supabase-js); Flask routes check the JWT with `@token_required` |
| **Billing** | Prepaid CHF balance via Stripe Checkout (one-time or monthly). Chat and indexing are deducted from the tenant owner's balance; Stripe credits are idempotent (`processed_payments`) |
| **Insights** | Per-tenant message volume chart and conversation viewer (owner only) |
| **Sharing** | End users can share a conversation via a 24 h link (`/share/:id`) |
| **i18n** | Vue i18n with locale files under `frontend/src/locales/` (en, de, fr) |

---

## Architecture

```
 customer site ── widget.js ──▶ iframe /chat/:tenantId?widget
                                        │
 ┌────────────┐  /api/  ┌───────────────▼────────────┐
 │ nginx (TLS)│────────▶│ api: Flask + gunicorn      │◀── Stripe webhooks
 │            │  /      │ (gthread, 8×16)            │
 │            │────────▶│ frontend: static SPA       │
 └────────────┘         └──────┬──────────┬──────────┘
                    Supabase ◀─┘          │ Celery (Redis broker)
                    (auth + PG)           ▼
          ┌──────────────┬────────────────┬──────────────┐
          │ worker_fast  │ worker_heavy   │ worker_chat  │  beat
          │ files, soup  │ Playwright     │ Gemini chat  │  (scheduler)
          └──────┬───────┴───────┬────────┴──────┬───────┘
                 └───────────────┴───────────────┴──▶ Gemini File Search
```

Each service lives in `backend/services/<name>/` with its own Dockerfile and
`requirements.txt`. Code used by more than one service lives in
`backend/shared/` (auth, database client, models, logging, Gemini store,
billing, URL guard, soup extractor). It is symlinked into each service's
`app/` for local development and copied into the image by the Dockerfiles.

**Flask blueprints (api service):**

| Blueprint | Prefix | Responsibilities |
|---|---|---|
| `auth_bp` | `/api/auth` | Change password (login/signup happen in supabase-js) |
| `tenants_bp` | `/api/tenants` | Tenant CRUD, public tenant config |
| `sources_bp` | `/api/tenants` | File upload, URL crawl, link discovery, crawl jobs |
| `widget_bp` | `/api/tenants` | Embeddable `widget.js` |
| `chat_bp` | `/api/chat` | Public chat + task polling, share links, owner-only insights |
| `billing_bp` | `/api/billing` | Balance, usage, Stripe checkout, portal, webhooks |

**Celery tasks:**

| Task | Worker | Trigger |
|---|---|---|
| `chat_task` | worker_chat | `POST /api/chat/<tenant>` |
| `process_local_file` | worker_fast | File upload route |
| `process_urls` / `process_file_url` | worker_fast | URL route, files found while crawling |
| `crawl_links_task` → `process_single_url_task` | worker_heavy | Link discovery route |
| `job_scheduler_task` | worker_fast | Celery Beat every 30 s |
| `zombie_reaper_task` | worker_fast | Celery Beat |

**Security notes:**

- Every route is either explicitly public or requires a token; `backend/tests/test_security.py` walks the URL map and fails if a new route is neither.
- All outbound fetches of user-supplied URLs go through `shared/security/url_guard.py`, which rejects non-public addresses, including on redirects.
- Never call `sign_in_*` / `sign_out` on the shared service-role Supabase client (see `shared/auth/routes.py`).

---

## Local Development

### Prerequisites

- Docker & Docker Compose

### 1. Configure Environment Variables

Create `.env` in the repo root with:

```env
# Supabase
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_KEY=<your-service-key>
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>

# Google Gemini
GOOGLE_API_KEY=<your-google-api-key>

# Flask
SECRET_KEY=<random-hex-string>   # python -c "import secrets; print(secrets.token_hex(32))"

# Models (optional — defaults shown)
CHAT_GEMINI_MODEL=gemini-3.1-flash-lite-preview

# Pricing (optional) — CHF per 1M tokens charged for indexing
INDEXING_RATE_CHF_PER_1M_TOKENS=0.15

# Stripe (use test keys locally)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:5173
```

Apply the database migrations in `supabase/migrations/` (e.g. `supabase db push`).

### 2. Start the Stack

```sh
docker compose up --build
```

> ⚠️ The first build downloads Playwright/Chromium browsers for web crawling and can take several minutes.

| Service | URL |
|---|---|
| Frontend dashboard | http://localhost:5173 (hot-reload) |
| Backend API | http://localhost:5000 (hot-reload) |
| Health check | http://localhost:5000/api/health |

### 3. Run the Tests

```sh
cd backend
pip install -r services/api/requirements.txt pytest
python -m pytest
```

CI (`.github/workflows/ci.yml`) runs the backend tests, a frontend build and `npm audit --audit-level=high` on every PR.

---

## Production Deployment

Production uses `docker-compose.prod.yml`:

- **api** runs under Gunicorn (8 gthread workers × 16 threads, 120 s timeout)
- **frontend** is built as a static bundle served by Nginx
- **nginx** terminates TLS and reverse-proxies `/api/` to the API and everything else to the frontend; `/chat/` is frameable from any origin for the widget
- All services have `restart: always`

| Script | Purpose |
|---|---|
| `./_prod_deploy.sh` | rsync the repo to the server, provision TLS if needed, rebuild and restart all services |
| `./_prod_frontend_deploy.sh` | Rebuild and restart only the frontend |
| `./_prod_logs.sh` | Tail service logs on the server |
| `./_restart_docker.sh` | Restart the stack |

---

## Frontend Views

| Route | Component | Description |
|---|---|---|
| `/login`, `/signup` | `Login.vue`, `Signup.vue` | Supabase email/password auth |
| `/manage-tenants` | `ManageTenants.vue` | Create / manage tenants |
| `/tenant/:id/sources` | `tenant/Sources.vue` | Knowledge sources and crawl jobs |
| `/tenant/:id/configure` | `tenant/Settings.vue` | Persona, behaviour, appearance |
| `/tenant/:id/insights` | `Insights.vue` | Message volume and conversation viewer |
| `/tenant/:id/install` | `Install.vue` | Widget embed snippet |
| `/chat/:tenantId` | `Chat.vue` | Full-page / widget chat |
| `/share/:shareId` | `ShareView.vue` | Shared conversation |
| `/subscription` | `Subscription.vue` | Balance, top-up, usage, billing history |
| `/profile` | `Profile.vue` | Account settings |
