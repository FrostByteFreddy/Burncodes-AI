# Database (Supabase Postgres)

Schema: `supabase/migrations/20261024000000_schema.sql`, one idempotent file
(`IF NOT EXISTS`, `CREATE OR REPLACE`): re-running it is safe. Changes go into
this file and are run in the Supabase SQL editor **before** the deploy that
needs them (the deploy script doesn't migrate). The backend uses the
service-role key (bypasses RLS).

## Tables

| Table | Holds |
|---|---|
| `tenants` | one row per chatbot: owner `user_id`, persona/template, `widget_config`, `is_active`, `test_password_hash`, `audience` (municipality/general), `learning_model`, crawl settings (`crawl_mode`, `crawl_exclusions`, `auto_recrawl`, `recrawl_interval_days`), `review_chats`, `calendar_feeds`, `contact_card`, `gemini_file_store_name` |
| `tenant_fine_tune` | trigger → instruction rules |
| `tenant_sources` | one row per page/file/upload: `source_location`, `source_type` (URL, FILE_URL, FILE), `status` (QUEUED, PROCESSING, COMPLETED, SKIPPED, ERROR, UNSUPPORTED), `content_hash`/`pending_hash`, `content_markdown`, `gemini_document_names`, costs/tokens, `last_job_id`/`learned_job_id`, `missed_crawls`, title/summary/importance/warnings |
| `crawling_jobs` | runs: `start_url`, options (`max_depth`, `excluded_urls`, `same_language`, `use_sitemap`, `skip_funnel`, `single_page_only`), `status`, `estimate` (JSON), `report` (JSON), `learning_model`, `trigger`, `auto_confirm` |
| `crawling_tasks` | one per URL of a run: `status`, `outcome`, `depth`, `attempts`, `enqueued_at` |
| `crawl_job_log` | the live activity log (event code + data; the dashboard words it) |
| `tenant_facts` | learned values: kind, label, value, validity, `source_id` |
| `tenant_events` | one row per dated event (series, zone, date, exception), `source_id` = most specific page (`source_rank`) |
| `chat_logs` | every answer: question, answer, tokens, `cost_chf`, `conversation_id` |
| `shared_conversations` | share links |
| `chat_reviews` / `chat_findings` | nightly review results |
| `user_billing` | `balance_chf` (4 decimals), Stripe customer/subscription |
| `processed_payments` | Stripe objects already credited |
| `billing_ledger` | every top-up and charge (see `billing.md`) |

Deleting a chatbot cascades to runs, logs, chats, reviews, facts and dates;
`billing_ledger` keeps its rows (`tenant_id` → NULL, `tenant_name` stays).

## Functions

`charge`, `apply_payment`, `credit_balance`, `deduct_balance` (money);
`upsert_events`, `release_source_events`, `event_key_of` (dates);
`analytics_time_buckets`, `conversation_summaries`, `usage_totals` (insights).

## Access

- `REVOKE ALL` from anon/authenticated, then `GRANT SELECT` on `tenants`,
  `crawling_jobs`, `crawling_tasks`, `crawl_job_log` only: needed for Realtime
  (the dashboard's live crawl progress), which delivers only rows that pass
  SELECT RLS. Owner policies limit those to the user's own chatbots.
- Everything else is read and written through the API.
- Realtime publication: the tables the dashboard subscribes to are added to
  `supabase_realtime` at the end of the file.
