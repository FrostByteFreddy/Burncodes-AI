---
name: burncodes-codebase
description: Map of the Burncodes AI codebase (ai.burn.codes): where each part lives, how crawling, learning, chat answers, billing, the dashboard and deployment work, and the pitfalls that have bitten before. Use before changing or debugging anything in this repository, or when asked where something is or how something works here.
---

# Burncodes AI — where what is

Chatbots for organisations' websites (Swiss municipalities, course platforms,
clubs). A crawl reads the site for free → an estimate → the customer pays →
Gemini learns every page → a chat widget answers with sources, dates and facts.

## The map

| You need to… | Look in |
|---|---|
| change what a crawl follows, its pace or its limits | `backend/services/worker_heavy/app/data_processing/tasks/crawl_tasks.py`, `backend/shared/knowledge/{url_scope,sitemap,politeness}.py` |
| change the job lifecycle (scan → estimate → learn → report) | `backend/shared/knowledge/jobs.py` |
| change what learning extracts or how it's charged | `backend/shared/knowledge/{learn,understanding,markdown,pdf_crosscheck}.py` |
| change chat answers (prompt, dates, facts, links) | `backend/services/worker_chat/app/chat/tasks.py`, `backend/shared/knowledge/{facts,names,contact,calendar}.py` |
| add or change an API endpoint | `backend/services/api/app/{tenants,chat,billing}/`, `backend/shared/auth/routes.py` |
| change prices, models, rates | `backend/shared/ai_models.py` (+ `.env`) |
| change balance, charges, Stripe | `backend/shared/billing/services.py`, `backend/services/api/app/billing/` |
| change the database | `supabase/migrations/20261024000000_schema.sql` (one idempotent file) |
| change a dashboard screen | `frontend/src/views/`, `frontend/src/components/tenant/` |
| change the look | `frontend/src/assets/tokens.css`, `bc.css`, `components/ui/Bc*.vue` |
| change dashboard text | `frontend/src/locales/{de,en,fr}.json` |
| deploy / check production | `_prod_deploy.sh`, `docker-compose.prod.yml`, see `references/operations.md` |

Details per area — read the one you need:

- `references/backend.md` — services, shared modules, API routes, Celery tasks
- `references/knowledge-pipeline.md` — crawl, estimate, learn, re-crawl, delete; the Gemini invariant
- `references/chat.md` — how an answer is put together, what the model is given
- `references/billing.md` — balance, ledger, prices, Stripe
- `references/database.md` — tables, functions, RLS and grants
- `references/frontend.md` — routes, stores, composables, design system, i18n rules
- `references/operations.md` — local stack, tests, deploy, production checks

## Rules that have bitten before

1. **The chat worker's Dockerfile copies knowledge modules one by one.** A new
   `from app.knowledge.X import` in `worker_chat` needs a `COPY` line in
   `backend/services/worker_chat/Dockerfile`, or every chat dies on import in
   production (happened 2026-10-30). `backend/tests/test_images.py` checks it.
   New shared modules also need a symlink in each service's `app/` for local use.
2. **Gemini first, database second.** Delete a File Search document or store,
   check the result (`delete_document` / `delete_store` return `False` instead
   of raising), and only then delete the row that names it. A row deleted first
   leaves documents nobody can find again, and the bot keeps answering from them.
   Deleting a document needs `config={"force": True}`.
3. **Requests end after 120 s** (nginx + gunicorn). Anything that may take
   longer runs in rounds (see `delete_crawling_job`: 60 s budget, answers 202,
   the client repeats) or as a Celery task.
4. **The local backend containers don't reload.** Their code is baked into the
   image: rebuild, or `docker cp` a changed file into the container for a quick
   test. Copying by hand also hides missing `COPY` lines (rule 1): build the
   image the way the server does before trusting a new module.
5. **The local `.env` points at the production database.** Never start
   `celery_beat` locally (scheduled re-crawls and reviews would run twice), and
   treat local test chats as real data (they land in `chat_logs`).
6. **`_prod_deploy.sh` ships the working tree**, uncommitted changes included,
   and does not run migrations: run new SQL in the Supabase SQL editor first.
7. **Realtime only delivers tables `authenticated` may SELECT** (tenants,
   crawling_jobs, crawling_tasks, crawl_job_log). Everything else is read
   through the API with the service role; users can't write tables directly.
8. **Chat must answer in ~5 s.** Stay on fast models (`gemini-3.1-flash-lite`);
   3.8 Flash took 8–15 s even with thinking "low". Improve answers through
   what the model is given (dates, facts, name hints), not a bigger model.
9. **Money is rounded to 4 decimals** in `BillingService.charge`, so balance and
   ledger never drift apart; anything that rounds to 0 isn't charged.
10. **Vue `<script setup>` order:** a composable that reads a ref must come
    after the `const` that declares it (a TDZ error broke the crawl page once).
11. **Copy in the dashboard is Swiss German:** "ss" not "ß", «» quotes, CHF
    with apostrophe thousands (`utils/format.js`). Write the user's language,
    not developer terms.

## Known open issues (audit 2026-10-29)

- The removed-page sweep (`jobs._mark_missed_sources`) counts fetch failures
  and other runs' pages as "missing" and deletes their knowledge after two crawls.
- `learn.py` ignores a failed delete of a page's old documents when re-learning.
- `get_or_create_store` can race when 8 learn tasks start at once.
- Account deletion ignores a failed store delete and a failed Stripe cancel.
- The prepaid check covers one run's estimate, not the balance across runs.
