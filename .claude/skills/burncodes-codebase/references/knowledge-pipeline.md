# Knowledge pipeline

Everything lives in `backend/shared/knowledge/` plus the crawl task in
`backend/services/worker_heavy/app/data_processing/tasks/crawl_tasks.py`.

## Job lifecycle (`jobs.py`)

```
IN_PROGRESS ──scan done──▶ SCANNED ──confirm (paid)──▶ INDEXING ──all learned──▶ COMPLETED
     │  free: fetch, convert,      estimate shown,        Gemini reads each          report on the job
     │  fingerprint, compare       customer picks model   new/changed source
     └──────────── stop / cancel ─────────────▶ FAILED ◀──── resume continues where it stopped
```

Transitions are conditional updates (`… WHERE status = X`): when several workers
finish together, exactly one moves the job on. Scheduled re-crawls
(`auto_confirm`) skip the confirmation up to `RECRAWL_AUTO_CONFIRM_MAX_CHF` if
the balance covers it.

## 1. Scan (worker_heavy, free)

`crawl_links_task` creates `crawling_jobs` + the first `crawling_tasks` row;
`process_single_url_task` handles one URL:

- **Scope** (`url_scope.py`): same site only, exclusion rules (path/host
  match), `same_language` (first path segment / lang params), `skip_funnel`
  (sign-up, thank-you pages), depth limit; documents count as files.
- **Sitemap** (`sitemap.py`): with `use_sitemap`, listed pages below the start
  address are added at the deepest level (≤ 5000).
- **Pace** (`politeness.py` + Redis): one shared slot schedule per website,
  `CRAWL_HOST_INTERVAL_MS` apart. 429/503 doubles the pause for an hour and
  honours Retry-After; a single timeout only retries its page; three timeouts
  within a minute slow the site down. Keys: `crawl:next:<host>`,
  `crawl:interval:<host>`, `crawl:timeouts:<host>`.
- **Record** (`jobs.record_scan`): one `tenant_sources` row per location;
  `pending_hash` vs `content_hash` decides new / changed / unchanged. Unchanged,
  learned pages cost nothing. `markdown.py` turns HTML/PDF into text and counts tokens.
- **Contact card** (`contact.py`): the footer's address, phone and hours, read
  once per crawl when the footer changed.

When the last task is done (`complete_scan_if_done`): removed-page sweep
(`_mark_missed_sources`), the customer's rules (`selection.apply_rules`), AI
triage of what isn't worth learning (`triage.py`, audience-aware via
`audience.py`), then the estimate (`compute_estimate`: tokens per source from a
calibration of recent real runs, priced for every learning model).

## 2. Confirm

`POST crawling_jobs/<id>/confirm {"model": "lite"|"argon"}`: balance must be ≥
that model's estimate; stores `learning_model`, starts `start_learning_task`.
Before that the customer can review `selection` (folders with costs) and
`skipped` (what triage set aside) and take things back in (`refresh_estimate`).

## 3. Learn (worker_fast, `learn.py`)

Per source, claimed QUEUED → PROCESSING:

1. job FAILED → back to QUEUED; owner balance ≤ 0 → ERROR 402.
2. `understanding.py`: one Gemini call with the chosen model returns sections,
   title/summary/importance, facts, schedules (dates), single events, warnings.
   PDFs over `INDEXING_MAX_PAGES` are made searchable only (`index_only_result`).
3. `_validate`: dates checked against the weekday rule; grid PDFs cross-checked
   by `pdf_crosscheck.py` (dates not printed in the grid are dropped or the
   series rejected).
4. `_index`: one File Search document per section (4 uploads in parallel),
   metadata `source_id` / `source_url`.
5. old documents deleted, facts (`tenant_facts`) and dates (`tenant_events`,
   `upsert_events`: one row per event however many pages name it) stored.
6. charged: `jobs.tokens_cost(in, out, embed, model)` → `BillingService.deduct_amount`.
7. row → COMPLETED with `gemini_document_names`, costs, tokens.

`finish_job_if_learned` (after every source) completes the job and builds the
report (`build_report`: highlights, schedules, issues, errors, cost).

## Re-crawls and removal

- `weekly_recrawl_task` re-runs each start address whose last run is older than
  the chatbot's `recrawl_interval_days`, with that run's options and model.
- `_mark_missed_sources`: pages of the host not seen by a full crawl get a
  miss; after 2 misses their documents and row are deleted. **Known issue:**
  failed fetches and pages only reachable from another run also count as missed.

## Deleting (Gemini first)

| What | Where | How |
|---|---|---|
| one source | `sources.delete_source` | its documents, then the file on disk (uploads), then the row |
| a run | `sources.delete_crawling_job` | marks it FAILED, deletes each batch's documents 16 at a time, then those rows; after 60 s answers 202 and the client repeats (`useCrawl.remove`) |
| all knowledge | `sources.delete_all_sources` | deletes the whole store, clears `gemini_file_store_name`, rows, jobs, uploads |
| a chatbot | `tenants/routes.delete_tenant` | store first (502 if Gemini refuses), then rows (cascade), uploads folder |

A row is only deleted once Gemini confirmed its documents are gone; on failure
the API answers 502 `gemini_failed` and the user retries. To find orphans,
compare `file_search_stores.documents.list(parent=store)` with all
`gemini_document_names` of the tenant's rows.

## Reports, review, branding

- `review.py`: nightly, reads conversations that went quiet, stores
  `chat_reviews` / `chat_findings` (unanswered, pushback, misunderstood), billed as `review`.
- `branding.py`: colours (theme-color first), logo (≤ 400 KB data URL) and name
  from the start page, for the widget.
