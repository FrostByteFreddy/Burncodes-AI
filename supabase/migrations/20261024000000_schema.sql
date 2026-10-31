-- ============================================================================
-- SwiftAnswer — complete database schema
--
-- Single source of truth for the public schema. Replaces all earlier
-- migrations. Written to be idempotent: on an empty Supabase project it
-- creates everything; on an existing project it only adds what is missing
-- and brings policies, grants and functions to the state described here.
--
-- Access model: the frontend talks to Supabase only for Auth and for
-- Realtime on the crawl tables. Everything else goes through the Flask API
-- with the service role, which enforces tenant ownership itself. Hence:
--   * anon has no table access at all
--   * authenticated may only SELECT crawling_jobs / crawling_tasks, and RLS
--     limits that to the user's own tenants (needed for Realtime)
--   * balance/aggregation functions are executable by service_role only
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Enum types
-- ----------------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE public.crawling_status AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE public.source_status AS ENUM ('QUEUED', 'PROCESSING', 'COMPLETED', 'ERROR', 'UNSUPPORTED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE public.source_type AS ENUM ('URL', 'FILE', 'FILE_URL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Values added after the types were first created on older projects
ALTER TYPE public.source_status ADD VALUE IF NOT EXISTS 'QUEUED';
ALTER TYPE public.source_status ADD VALUE IF NOT EXISTS 'UNSUPPORTED';
ALTER TYPE public.source_type ADD VALUE IF NOT EXISTS 'FILE_URL';
-- Sorted out before learning (archive, old versions …); can be taken back in
ALTER TYPE public.source_status ADD VALUE IF NOT EXISTS 'SKIPPED';
-- Crawl job phases: scan (IN_PROGRESS) → SCANNED (estimate, awaiting
-- confirmation) → INDEXING (Gemini reads changed pages) → COMPLETED
ALTER TYPE public.crawling_status ADD VALUE IF NOT EXISTS 'SCANNED';
ALTER TYPE public.crawling_status ADD VALUE IF NOT EXISTS 'INDEXING';

-- ----------------------------------------------------------------------------
-- Tables
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.tenants (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name                   TEXT NOT NULL,
    intro_message          TEXT,
    system_persona         TEXT,
    rag_prompt_template    TEXT,
    doc_language           TEXT,
    translation_target     TEXT,
    widget_config          JSONB DEFAULT '{}'::jsonb,
    crawl_mode             TEXT NOT NULL DEFAULT 'playwright_llm',
    gemini_file_store_name TEXT,
    created_at             TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS doc_language           TEXT;
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS translation_target     TEXT;
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS widget_config          JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS crawl_mode             TEXT NOT NULL DEFAULT 'playwright_llm';
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS gemini_file_store_name TEXT;
-- Opt-in automatic re-crawl; unchanged pages cost nothing thanks to content hashes
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS auto_recrawl          BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS recrawl_interval_days INTEGER NOT NULL DEFAULT 7;
-- Master switch: off = no widget anywhere, no public page, no answers (owner preview excepted)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS is_active             BOOLEAN NOT NULL DEFAULT true;
-- Review finished conversations for unanswered questions and pushback (billed per conversation)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS review_chats          BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS review_interval_days  INTEGER NOT NULL DEFAULT 1;
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS last_review_at        TIMESTAMPTZ;
-- Password for a chatbot still in development (werkzeug hash); NULL = open
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS test_password_hash    TEXT;
-- Residents can subscribe to validated dates as calendar feeds (.ics)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS calendar_feeds        BOOLEAN NOT NULL DEFAULT true;
-- address, phone, email and opening hours read from the website footer (start page)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS contact_card          JSONB;
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS contact_footer_hash   TEXT;
-- what the customer left out of learning (folders/sources); every crawl applies it
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS crawl_exclusions      JSONB NOT NULL DEFAULT '[]'::jsonb;
-- who the chatbot answers: 'municipality' (residents) or 'general' (visitors of any other website)
ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS audience              TEXT NOT NULL DEFAULT 'municipality'
    CHECK (audience IN ('municipality', 'general'));
COMMENT ON COLUMN public.tenants.gemini_file_store_name IS
    'Gemini File Search Store resource name (e.g. fileSearchStores/abc123). NULL until the tenant uploads their first source.';

CREATE TABLE IF NOT EXISTS public.tenant_fine_tune (
    id          SERIAL PRIMARY KEY,
    tenant_id   UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    trigger     TEXT NOT NULL,
    instruction TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public.tenant_sources (
    id                   SERIAL PRIMARY KEY,
    tenant_id            UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    source_type          public.source_type NOT NULL,
    source_location      TEXT NOT NULL,
    status               public.source_status NOT NULL DEFAULT 'PROCESSING',
    status_code          INTEGER,
    gemini_document_name TEXT,
    input_tokens         INTEGER,
    output_tokens        INTEGER,
    cost_chf             DECIMAL(10, 6),
    created_at           TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS status_code          INTEGER;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS gemini_document_name TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS input_tokens         INTEGER;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS output_tokens        INTEGER;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS cost_chf             DECIMAL(10, 6);
-- What Gemini understood about the source (crawl report, dashboard)
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS title                 TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS summary               TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS page_type             TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS importance            SMALLINT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS importance_reason     TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS warnings              JSONB NOT NULL DEFAULT '[]'::jsonb;
-- Change detection: content_hash = what is indexed, pending_hash = latest scan.
-- They differ exactly when the source needs (re-)learning.
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS content_markdown      TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS content_tokens        INTEGER;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS file_pages            INTEGER;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS content_hash          TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS pending_hash          TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS etag                  TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS last_modified         TEXT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS last_seen_at          TIMESTAMPTZ;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS last_changed_at       TIMESTAMPTZ;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS missed_crawls         INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS last_job_id           BIGINT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS learned_job_id        BIGINT;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS last_learn_cost_chf   DECIMAL(10, 6);
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS learn_started_at      TIMESTAMPTZ;
-- One File Search document per section (+ one for facts/dates)
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS gemini_document_names TEXT[] NOT NULL DEFAULT '{}';
-- Number of indexed chunks (= section documents) — shown in the dashboard
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS indexed_chunks        INTEGER;
-- Why a source was sorted out before learning (a fixed category, see knowledge/triage.py)
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS skip_reason           TEXT;
-- 'full' = read by Gemini; 'index_only' = long documents, text made searchable only
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS learn_mode            TEXT;
-- Tokens of the last learning run, to calibrate the cost estimate on real numbers
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS last_learn_in_tokens  INTEGER;
ALTER TABLE public.tenant_sources ADD COLUMN IF NOT EXISTS last_learn_out_tokens INTEGER;
COMMENT ON COLUMN public.tenant_sources.gemini_document_name IS
    'Gemini File Search document resource name. Used to delete the document when the source is removed.';

CREATE TABLE IF NOT EXISTS public.crawling_jobs (
    id            BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id     UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    start_url     TEXT NOT NULL,
    max_depth     INTEGER NOT NULL,
    status        public.crawling_status NOT NULL DEFAULT 'PENDING',
    excluded_urls TEXT[] DEFAULT '{}'::text[],
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS excluded_urls TEXT[] DEFAULT '{}'::text[];
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS single_page_only BOOLEAN NOT NULL DEFAULT false;
-- skip other language versions of the site (/de/…, /fr/…) than the one the crawl started in
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS same_language    BOOLEAN NOT NULL DEFAULT false;
-- also visit the pages the site's sitemap lists (landing pages no menu links to)
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS use_sitemap      BOOLEAN NOT NULL DEFAULT false;
-- skip thank-you, confirmation, error, ad-copy, cart and account pages
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS skip_funnel      BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS crawl_mode       TEXT;
-- 'manual' or 'scheduled'; scheduled re-crawls are pre-approved (auto_confirm)
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS trigger          TEXT NOT NULL DEFAULT 'manual';
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS auto_confirm     BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS estimate         JSONB;
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS report           JSONB;
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS confirmed_at     TIMESTAMPTZ;
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS finished_at      TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS public.crawling_tasks (
    id         BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    job_id     BIGINT NOT NULL REFERENCES public.crawling_jobs(id) ON DELETE CASCADE,
    url        TEXT NOT NULL,
    depth      INTEGER NOT NULL,
    status     public.crawling_status NOT NULL DEFAULT 'PENDING',
    parent_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.crawling_tasks ADD COLUMN IF NOT EXISTS parent_url TEXT;
-- Set whenever the task is put on the queue; the scheduler only re-sends
-- tasks whose message was evidently lost (old enqueued_at).
ALTER TABLE public.crawling_tasks ADD COLUMN IF NOT EXISTS enqueued_at TIMESTAMPTZ;
-- Scan result per URL: new / changed / unchanged / error / excluded / refused
ALTER TABLE public.crawling_tasks ADD COLUMN IF NOT EXISTS outcome TEXT;
-- how often the page was retried because the website said "too many requests"
ALTER TABLE public.crawling_tasks ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS public.chat_logs (
    id              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    conversation_id UUID NOT NULL,
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_message    TEXT NOT NULL,
    ai_message      TEXT NOT NULL,
    model_used      TEXT,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    cost_chf        DECIMAL(10, 6),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.chat_logs ADD COLUMN IF NOT EXISTS model_used    TEXT;
ALTER TABLE public.chat_logs ADD COLUMN IF NOT EXISTS input_tokens  INTEGER;
ALTER TABLE public.chat_logs ADD COLUMN IF NOT EXISTS output_tokens INTEGER;
ALTER TABLE public.chat_logs ADD COLUMN IF NOT EXISTS cost_chf      DECIMAL(10, 6);

-- One share link per conversation; served only through the API.
CREATE TABLE IF NOT EXISTS public.shared_conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL UNIQUE,
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '24 hours')
);

CREATE TABLE IF NOT EXISTS public.user_billing (
    user_id                UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    balance_chf            DECIMAL(10, 4) DEFAULT 0.0000,
    stripe_customer_id     TEXT,
    stripe_subscription_id TEXT,
    created_at             TIMESTAMPTZ DEFAULT now(),
    updated_at             TIMESTAMPTZ DEFAULT now()
);

-- Every Stripe object that added balance, keyed "checkout:<id>" / "invoice:<id>".
-- The primary key is what makes crediting idempotent (see apply_payment).
CREATE TABLE IF NOT EXISTS public.processed_payments (
    source_id  TEXT PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount_chf DECIMAL(10, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Live activity of a crawl job, shown in the dashboard (Realtime). Events are
-- codes + data so the frontend renders them in the user's language.
CREATE TABLE IF NOT EXISTS public.crawl_job_log (
    id         BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    job_id     BIGINT NOT NULL REFERENCES public.crawling_jobs(id) ON DELETE CASCADE,
    tenant_id  UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    event      TEXT NOT NULL,
    data       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Facts extracted from sources (opening hours, fees, contacts, deadlines, ...)
CREATE TABLE IF NOT EXISTS public.tenant_facts (
    id         BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id  UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    source_id  INTEGER NOT NULL REFERENCES public.tenant_sources(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL,
    label      TEXT NOT NULL,
    value      TEXT NOT NULL,
    valid_from DATE,
    valid_to   DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Validated dates (schedules such as waste collection, one-off events).
-- Answers "when is the next ..." deterministically in the chat.
CREATE TABLE IF NOT EXISTS public.tenant_events (
    id           BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id    UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    source_id    INTEGER NOT NULL REFERENCES public.tenant_sources(id) ON DELETE CASCADE,
    series       TEXT NOT NULL,
    zone         TEXT NOT NULL DEFAULT '',
    event_date   DATE NOT NULL,
    is_exception BOOLEAN NOT NULL DEFAULT false,
    notes        TEXT NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per reviewed conversation; a conversation that continues after
-- its review is reviewed again from last_log_id on.
CREATE TABLE IF NOT EXISTS public.chat_reviews (
    conversation_id UUID PRIMARY KEY,
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    last_log_id     BIGINT NOT NULL,
    reviewed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    cost_chf        DECIMAL(10, 6) NOT NULL DEFAULT 0
);

-- What the review found: questions the bot couldn't answer, answers people
-- pushed back on. Staff mark them resolved (knowledge added) or dismissed.
CREATE TABLE IF NOT EXISTS public.chat_findings (
    id              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,
    log_id          BIGINT,
    kind            TEXT NOT NULL CHECK (kind IN ('unanswered', 'wrong', 'pushback', 'unclear')),
    question        TEXT NOT NULL,
    problem         TEXT NOT NULL,
    suggestion      TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'dismissed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

-- ----------------------------------------------------------------------------
-- Legacy objects (pre-Gemini File Search pipeline) — unused by any code
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS public.tenant_knowledge;
DROP TABLE IF EXISTS public.app_logs;
ALTER TABLE public.tenant_sources   DROP COLUMN IF EXISTS readme;
ALTER TABLE public.tenant_sources   DROP COLUMN IF EXISTS chunk_count;
ALTER TABLE public.tenant_fine_tune DROP COLUMN IF EXISTS vector_id;

-- ----------------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_chat_logs_tenant_conversation ON public.chat_logs (tenant_id, conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_crawling_jobs_tenant          ON public.crawling_jobs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_crawling_jobs_status          ON public.crawling_jobs (status);
CREATE INDEX IF NOT EXISTS idx_crawling_tasks_job_id         ON public.crawling_tasks (job_id);
CREATE INDEX IF NOT EXISTS idx_crawling_tasks_status         ON public.crawling_tasks (status);
CREATE INDEX IF NOT EXISTS idx_tenant_sources_tenant         ON public.tenant_sources (tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenants_user                  ON public.tenants (user_id);
CREATE INDEX IF NOT EXISTS idx_processed_payments_user       ON public.processed_payments (user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_events_tenant_date ON public.tenant_events (tenant_id, event_date);
CREATE INDEX IF NOT EXISTS idx_crawl_job_log_job          ON public.crawl_job_log (job_id, id);
CREATE INDEX IF NOT EXISTS idx_crawl_job_log_tenant       ON public.crawl_job_log (tenant_id, id);
CREATE INDEX IF NOT EXISTS idx_tenant_events_source       ON public.tenant_events (source_id);
CREATE INDEX IF NOT EXISTS idx_tenant_facts_source        ON public.tenant_facts (source_id);
CREATE INDEX IF NOT EXISTS idx_tenant_sources_last_job    ON public.tenant_sources (last_job_id);
ALTER TABLE public.chat_findings ADD COLUMN IF NOT EXISTS topic TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_chat_reviews_tenant        ON public.chat_reviews (tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_findings_tenant       ON public.chat_findings (tenant_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_logs_tenant_created   ON public.chat_logs (tenant_id, created_at);

-- A crawl job visits each URL once. Earlier versions re-queued tasks and
-- produced duplicate rows; keep the oldest before enforcing uniqueness.
DELETE FROM public.crawling_tasks a
    USING public.crawling_tasks b
    WHERE a.job_id = b.job_id AND a.url = b.url AND a.id > b.id;
CREATE UNIQUE INDEX IF NOT EXISTS uq_crawling_tasks_job_url ON public.crawling_tasks (job_id, url);

-- One source row per tenant and location. Legacy duplicates must be removed
-- first by backend/scripts/dedupe_sources.py (it also deletes their indexed
-- documents in Gemini); until then the index is skipped instead of failing.
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.tenant_sources
        GROUP BY tenant_id, source_location HAVING count(*) > 1
    ) THEN
        CREATE UNIQUE INDEX IF NOT EXISTS uq_tenant_sources_location ON public.tenant_sources (tenant_id, source_location);
    ELSE
        RAISE NOTICE 'tenant_sources has duplicate locations — run backend/scripts/dedupe_sources.py, then re-apply this migration';
    END IF;
END $$;

-- Redundant with the primary key
DROP INDEX IF EXISTS public.idx_shared_conversations_id;

-- ----------------------------------------------------------------------------
-- Triggers
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_crawling_jobs_updated_at
    BEFORE UPDATE ON public.crawling_jobs
    FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

CREATE OR REPLACE TRIGGER trg_crawling_tasks_updated_at
    BEFORE UPDATE ON public.crawling_tasks
    FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

-- ----------------------------------------------------------------------------
-- Functions (RPC) — called by the backend with the service role
-- ----------------------------------------------------------------------------

-- Atomically deduct from balance. Returns the new balance, or -1 if the user has no row.
CREATE OR REPLACE FUNCTION public.deduct_balance(p_user_id UUID, p_amount DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    v_new_balance DECIMAL;
BEGIN
    UPDATE public.user_billing
    SET balance_chf = balance_chf - p_amount,
        updated_at  = now()
    WHERE user_id = p_user_id
    RETURNING balance_chf INTO v_new_balance;

    IF NOT FOUND THEN
        RETURN -1;
    END IF;
    RETURN v_new_balance;
END;
$$ LANGUAGE plpgsql;

-- Atomically credit balance (creates the row if needed). Returns the new balance.
CREATE OR REPLACE FUNCTION public.credit_balance(p_user_id UUID, p_amount DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    v_new_balance DECIMAL;
BEGIN
    INSERT INTO public.user_billing (user_id, balance_chf, updated_at)
    VALUES (p_user_id, p_amount, now())
    ON CONFLICT (user_id) DO UPDATE
    SET balance_chf = public.user_billing.balance_chf + p_amount,
        updated_at  = now()
    RETURNING balance_chf INTO v_new_balance;

    RETURN v_new_balance;
END;
$$ LANGUAGE plpgsql;

-- Credits a Stripe payment at most once. Returns TRUE if this call credited.
CREATE OR REPLACE FUNCTION public.apply_payment(p_source_id TEXT, p_user_id UUID, p_amount DECIMAL)
RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO public.processed_payments (source_id, user_id, amount_chf)
    VALUES (p_source_id, p_user_id, p_amount)
    ON CONFLICT (source_id) DO NOTHING;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    PERFORM public.credit_balance(p_user_id, p_amount);
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Message counts per time bucket for the Insights chart.
CREATE OR REPLACE FUNCTION public.analytics_time_buckets(
    p_tenant_id  UUID,
    p_start_time TIMESTAMPTZ,
    p_interval   TEXT DEFAULT '1 hour'
)
RETURNS TABLE(time_bucket TIMESTAMPTZ, message_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        date_trunc(
            CASE
                WHEN p_interval = 'minute' THEN 'minute'
                WHEN p_interval = '1 day'  THEN 'day'
                ELSE 'hour'
            END,
            cl.created_at
        ) AS time_bucket,
        COUNT(*)::BIGINT AS message_count
    FROM public.chat_logs cl
    WHERE cl.tenant_id = p_tenant_id
      AND cl.created_at >= p_start_time
    GROUP BY 1
    ORDER BY 1;
END;
$$ LANGUAGE plpgsql STABLE;

-- One row per conversation, newest first (no PostgREST 1000-row truncation).
CREATE OR REPLACE FUNCTION public.conversation_summaries(p_tenant_id UUID)
RETURNS TABLE(
    conversation_id UUID,
    last_active     TIMESTAMPTZ,
    message_count   BIGINT,
    total_cost      NUMERIC,
    first_message   TEXT
) AS $$
    SELECT
        cl.conversation_id,
        MAX(cl.created_at),
        COUNT(*)::BIGINT,
        COALESCE(SUM(cl.cost_chf), 0),
        (ARRAY_AGG(cl.user_message ORDER BY cl.created_at))[1]
    FROM public.chat_logs cl
    WHERE cl.tenant_id = p_tenant_id
    GROUP BY cl.conversation_id
    ORDER BY 2 DESC;
$$ LANGUAGE sql STABLE;

-- Usage totals across all of a user's tenants, split into chat and indexing.
CREATE OR REPLACE FUNCTION public.usage_totals(p_user_id UUID)
RETURNS TABLE(
    chat_cost      NUMERIC,
    chat_input     BIGINT,
    chat_output    BIGINT,
    sources_cost   NUMERIC,
    sources_input  BIGINT,
    sources_output BIGINT
) AS $$
    WITH owned AS (
        SELECT id FROM public.tenants WHERE user_id = p_user_id
    )
    SELECT
        (SELECT COALESCE(SUM(cost_chf), 0)      FROM public.chat_logs      WHERE tenant_id IN (SELECT id FROM owned)),
        (SELECT COALESCE(SUM(input_tokens), 0)  FROM public.chat_logs      WHERE tenant_id IN (SELECT id FROM owned))::BIGINT,
        (SELECT COALESCE(SUM(output_tokens), 0) FROM public.chat_logs      WHERE tenant_id IN (SELECT id FROM owned))::BIGINT,
        (SELECT COALESCE(SUM(cost_chf), 0)      FROM public.tenant_sources WHERE tenant_id IN (SELECT id FROM owned)),
        (SELECT COALESCE(SUM(input_tokens), 0)  FROM public.tenant_sources WHERE tenant_id IN (SELECT id FROM owned))::BIGINT,
        (SELECT COALESCE(SUM(output_tokens), 0) FROM public.tenant_sources WHERE tenant_id IN (SELECT id FROM owned))::BIGINT;
$$ LANGUAGE sql STABLE;

-- ----------------------------------------------------------------------------
-- Dates: one row per event, however many pages name it
-- ----------------------------------------------------------------------------
-- An event on the home page, the event list and its own page is one row.
-- source_ids are all pages that name it; source_id is the one to cite (the
-- most specific, source_rank). A page that is re-learned or deleted only
-- leaves the list; the row goes when no page names the event any more.

-- name + zone, ignoring quote style, case and spacing (as the app's event_key)
CREATE OR REPLACE FUNCTION public.event_key_of(p_series TEXT, p_zone TEXT)
RETURNS TEXT AS $$
    SELECT lower(regexp_replace(translate(normalize(coalesce(p_series, ''), NFKC), '„“”«»‹›‚‘’''', '"""""""""""'), '\s+', ' ', 'g'))
        || '|' ||
           lower(regexp_replace(translate(normalize(coalesce(p_zone, ''), NFKC), '„“”«»‹›‚‘’''', '"""""""""""'), '\s+', ' ', 'g'));
$$ LANGUAGE sql IMMUTABLE;

ALTER TABLE public.tenant_events ADD COLUMN IF NOT EXISTS source_ids  INTEGER[] NOT NULL DEFAULT '{}';
ALTER TABLE public.tenant_events ADD COLUMN IF NOT EXISTS source_rank SMALLINT  NOT NULL DEFAULT 0;
ALTER TABLE public.tenant_events ADD COLUMN IF NOT EXISTS event_key   TEXT
    GENERATED ALWAYS AS (public.event_key_of(series, zone)) STORED;
UPDATE public.tenant_events SET source_ids = ARRAY[source_id] WHERE source_ids = '{}';

-- merge rows stored per page before (keep the oldest, collect all pages)
UPDATE public.tenant_events t
   SET source_ids = m.ids, is_exception = m.exc
  FROM (SELECT tenant_id, event_key, event_date, min(id) AS keep_id,
               array_agg(DISTINCT s) AS ids, bool_or(is_exception) AS exc
          FROM public.tenant_events, unnest(source_ids) s
         GROUP BY tenant_id, event_key, event_date
        HAVING count(DISTINCT id) > 1) m
 WHERE t.id = m.keep_id;
DELETE FROM public.tenant_events a
 USING public.tenant_events b
 WHERE a.tenant_id = b.tenant_id AND a.event_key = b.event_key AND a.event_date = b.event_date AND a.id > b.id;
CREATE UNIQUE INDEX IF NOT EXISTS uq_tenant_events_key ON public.tenant_events (tenant_id, event_key, event_date);
CREATE INDEX IF NOT EXISTS idx_tenant_events_source_ids ON public.tenant_events USING gin (source_ids);

-- Stores a page's dates: new events are inserted, known ones gain the page.
-- p_rows: [{tenant_id, source_id, source_rank, series, zone, event_date, is_exception, notes}]
CREATE OR REPLACE FUNCTION public.upsert_events(p_rows JSONB)
RETURNS VOID AS $$
    INSERT INTO public.tenant_events AS t
           (tenant_id, source_id, source_ids, source_rank, series, zone, event_date, is_exception, notes)
    SELECT DISTINCT ON (r->>'tenant_id', public.event_key_of(r->>'series', r->>'zone'), (r->>'event_date')::date)
           (r->>'tenant_id')::uuid, (r->>'source_id')::int, ARRAY[(r->>'source_id')::int],
           coalesce((r->>'source_rank')::int, 0), coalesce(r->>'series', ''), coalesce(r->>'zone', ''),
           (r->>'event_date')::date, coalesce((r->>'is_exception')::boolean, false), coalesce(r->>'notes', '')
      FROM jsonb_array_elements(p_rows) r
    ON CONFLICT (tenant_id, event_key, event_date) DO UPDATE SET
        source_ids   = (SELECT array_agg(DISTINCT x) FROM unnest(t.source_ids || EXCLUDED.source_ids) x),
        source_id    = CASE WHEN EXCLUDED.source_rank > t.source_rank THEN EXCLUDED.source_id ELSE t.source_id END,
        source_rank  = GREATEST(t.source_rank, EXCLUDED.source_rank),
        is_exception = t.is_exception OR EXCLUDED.is_exception,
        notes        = CASE WHEN length(EXCLUDED.notes) > length(t.notes) THEN EXCLUDED.notes ELSE t.notes END;
$$ LANGUAGE sql;

-- A page no longer names its dates (re-learned or deleted): it leaves their
-- page lists; dates no other page names go, the rest cite another page.
CREATE OR REPLACE FUNCTION public.release_source_events(p_source INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE public.tenant_events SET source_ids = array_remove(source_ids, p_source) WHERE source_ids @> ARRAY[p_source];
    DELETE FROM public.tenant_events WHERE source_id = p_source AND cardinality(source_ids) = 0;
    UPDATE public.tenant_events SET source_id = source_ids[1], source_rank = 0 WHERE source_id = p_source;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.release_events_of_deleted_source()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM public.release_source_events(OLD.id);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_release_source_events ON public.tenant_sources;
CREATE TRIGGER trg_release_source_events BEFORE DELETE ON public.tenant_sources
    FOR EACH ROW EXECUTE FUNCTION public.release_events_of_deleted_source();

-- ----------------------------------------------------------------------------
-- Money ledger: every top-up and every charge is one row, so spend survives
-- deleted runs and chatbots, and the balance always equals the ledger's sum.
-- ----------------------------------------------------------------------------
-- the learning model the customer chose for a run, and a chatbot's default
-- ('lite', 'argon'; see ai_models.LEARNING_MODELS)
ALTER TABLE public.crawling_jobs ADD COLUMN IF NOT EXISTS learning_model TEXT;
ALTER TABLE public.tenants       ADD COLUMN IF NOT EXISTS learning_model TEXT;

CREATE TABLE IF NOT EXISTS public.billing_ledger (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    -- the chatbot it was spent on; kept by name when the chatbot is deleted
    tenant_id   UUID REFERENCES public.tenants(id) ON DELETE SET NULL,
    tenant_name TEXT,
    -- topup · answer · learning · review · opening (balance before the ledger existed)
    kind        TEXT NOT NULL,
    -- positive credits the balance, negative spends it
    amount_chf  DECIMAL(12, 6) NOT NULL,
    ref         TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_billing_ledger_user   ON public.billing_ledger (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_billing_ledger_tenant ON public.billing_ledger (tenant_id, created_at);
ALTER TABLE public.billing_ledger ENABLE ROW LEVEL SECURITY;

-- Spends from the balance and books it in one step. Returns the new balance, -1 without a billing row.
CREATE OR REPLACE FUNCTION public.charge(p_user_id UUID, p_tenant_id UUID, p_kind TEXT, p_amount DECIMAL, p_ref TEXT DEFAULT NULL)
RETURNS DECIMAL AS $$
DECLARE
    v_new_balance DECIMAL;
BEGIN
    UPDATE public.user_billing SET balance_chf = balance_chf - p_amount, updated_at = now()
     WHERE user_id = p_user_id RETURNING balance_chf INTO v_new_balance;
    IF NOT FOUND THEN
        RETURN -1;
    END IF;
    INSERT INTO public.billing_ledger (user_id, tenant_id, tenant_name, kind, amount_chf, ref)
    VALUES (p_user_id, p_tenant_id, (SELECT name FROM public.tenants WHERE id = p_tenant_id), p_kind, -p_amount, p_ref);
    RETURN v_new_balance;
END;
$$ LANGUAGE plpgsql;

-- Credits a Stripe payment at most once, and books it. Returns TRUE if this call credited.
CREATE OR REPLACE FUNCTION public.apply_payment(p_source_id TEXT, p_user_id UUID, p_amount DECIMAL)
RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO public.processed_payments (source_id, user_id, amount_chf)
    VALUES (p_source_id, p_user_id, p_amount)
    ON CONFLICT (source_id) DO NOTHING;
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    PERFORM public.credit_balance(p_user_id, p_amount);
    INSERT INTO public.billing_ledger (user_id, kind, amount_chf, ref) VALUES (p_user_id, 'topup', p_amount, p_source_id);
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Backfill once from the records kept so far, then an opening row per account
-- so that the ledger's sum equals today's balance.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.billing_ledger) THEN
        INSERT INTO public.billing_ledger (user_id, tenant_id, tenant_name, kind, amount_chf, ref, created_at)
        SELECT t.user_id, t.id, t.name, 'answer', -SUM(c.cost_chf), 'backfill', date_trunc('day', c.created_at)
          FROM public.chat_logs c JOIN public.tenants t ON t.id = c.tenant_id
         WHERE c.cost_chf > 0 GROUP BY t.user_id, t.id, t.name, date_trunc('day', c.created_at);
        INSERT INTO public.billing_ledger (user_id, tenant_id, tenant_name, kind, amount_chf, ref, created_at)
        SELECT t.user_id, t.id, t.name, 'review', -SUM(r.cost_chf), 'backfill', date_trunc('day', r.reviewed_at)
          FROM public.chat_reviews r JOIN public.tenants t ON t.id = r.tenant_id
         WHERE r.cost_chf > 0 GROUP BY t.user_id, t.id, t.name, date_trunc('day', r.reviewed_at);
        INSERT INTO public.billing_ledger (user_id, tenant_id, tenant_name, kind, amount_chf, ref, created_at)
        SELECT t.user_id, t.id, t.name, 'learning', -SUM(s.cost_chf), 'backfill',
               date_trunc('day', COALESCE(s.last_changed_at, s.created_at))
          FROM public.tenant_sources s JOIN public.tenants t ON t.id = s.tenant_id
         WHERE s.cost_chf > 0 GROUP BY t.user_id, t.id, t.name, date_trunc('day', COALESCE(s.last_changed_at, s.created_at));
        INSERT INTO public.billing_ledger (user_id, kind, amount_chf, ref, created_at)
        SELECT user_id, 'topup', amount_chf, source_id, created_at FROM public.processed_payments;
        INSERT INTO public.billing_ledger (user_id, kind, amount_chf, ref)
        SELECT b.user_id, 'opening', b.balance_chf - COALESCE((SELECT SUM(l.amount_chf) FROM public.billing_ledger l WHERE l.user_id = b.user_id), 0), 'backfill'
          FROM public.user_billing b;
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- Row Level Security
-- ----------------------------------------------------------------------------

ALTER TABLE public.tenants              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_fine_tune     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_sources       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crawling_jobs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crawling_tasks       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_logs            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shared_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_billing         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processed_payments   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_facts         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_events        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crawl_job_log        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_reviews         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_findings        ENABLE ROW LEVEL SECURITY;

-- Policies are recreated so their definition here is authoritative.
DROP POLICY IF EXISTS "Allow users to view their own tenants"                   ON public.tenants;
DROP POLICY IF EXISTS "Allow users to create their own tenants"                 ON public.tenants;
DROP POLICY IF EXISTS "Allow users to update their own tenants"                 ON public.tenants;
DROP POLICY IF EXISTS "Allow users to delete their own tenants"                 ON public.tenants;
DROP POLICY IF EXISTS "Allow users to manage fine_tune rules for their tenants" ON public.tenant_fine_tune;
DROP POLICY IF EXISTS "Allow users to manage sources for their tenants"         ON public.tenant_sources;
DROP POLICY IF EXISTS "Allow tenant owner to read their own logs"               ON public.chat_logs;
DROP POLICY IF EXISTS "Users can view their own billing"                        ON public.user_billing;
-- Previously allowed anyone with the anon key to list all shares, insert
-- shares for arbitrary conversations, and read shared transcripts directly.
-- Shares are served exclusively by the API (service role).
DROP POLICY IF EXISTS "shared_conversations_public_read"    ON public.shared_conversations;
DROP POLICY IF EXISTS "shared_conversations_service_insert" ON public.shared_conversations;
DROP POLICY IF EXISTS "chat_logs_shared_public_read"        ON public.chat_logs;
DROP POLICY IF EXISTS "crawling_jobs_owner_read"            ON public.crawling_jobs;
DROP POLICY IF EXISTS "crawling_tasks_owner_read"           ON public.crawling_tasks;
DROP POLICY IF EXISTS "crawl_job_log_owner_read"            ON public.crawl_job_log;

-- Owner policies. authenticated only has SELECT on tenants and the crawl
-- tables (see Grants); the rest keep RLS meaningful if grants are ever added.
CREATE POLICY "Allow users to view their own tenants"   ON public.tenants FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Allow users to create their own tenants" ON public.tenants FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Allow users to update their own tenants" ON public.tenants FOR UPDATE TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Allow users to delete their own tenants" ON public.tenants FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "Allow users to manage fine_tune rules for their tenants" ON public.tenant_fine_tune TO authenticated
    USING (EXISTS (SELECT 1 FROM public.tenants t WHERE t.id = tenant_fine_tune.tenant_id AND t.user_id = auth.uid()));

CREATE POLICY "Allow users to manage sources for their tenants" ON public.tenant_sources TO authenticated
    USING (EXISTS (SELECT 1 FROM public.tenants t WHERE t.id = tenant_sources.tenant_id AND t.user_id = auth.uid()));

CREATE POLICY "Allow tenant owner to read their own logs" ON public.chat_logs FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM public.tenants t WHERE t.id = chat_logs.tenant_id AND t.user_id = auth.uid()));

CREATE POLICY "Users can view their own billing" ON public.user_billing FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

-- Realtime (crawl progress in the dashboard) delivers only rows that pass
-- SELECT RLS, so owners need read access to their own crawl rows.
CREATE POLICY "crawling_jobs_owner_read" ON public.crawling_jobs FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM public.tenants t WHERE t.id = crawling_jobs.tenant_id AND t.user_id = auth.uid()));

CREATE POLICY "crawling_tasks_owner_read" ON public.crawling_tasks FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM public.crawling_jobs j JOIN public.tenants t ON t.id = j.tenant_id
        WHERE j.id = crawling_tasks.job_id AND t.user_id = auth.uid()
    ));

CREATE POLICY "crawl_job_log_owner_read" ON public.crawl_job_log FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM public.tenants t WHERE t.id = crawl_job_log.tenant_id AND t.user_id = auth.uid()));

-- processed_payments and shared_conversations: no policies (service role only).
-- tenant_facts and tenant_events: no policies (served through the API).
-- chat_reviews and chat_findings: no policies (served through the API).

-- ----------------------------------------------------------------------------
-- Grants
-- ----------------------------------------------------------------------------

REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC, anon, authenticated;

GRANT ALL ON ALL TABLES    IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Realtime on the crawl tables; the crawl RLS policies look up tenant
-- ownership, so tenants must be readable too (RLS limits it to own rows).
GRANT SELECT ON public.tenants, public.crawling_jobs, public.crawling_tasks, public.crawl_job_log TO authenticated;

-- Trigger functions run as the table owner regardless of grants, but
-- rls_auto_enable (platform event trigger, if present) must stay callable.
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'rls_auto_enable' AND pronamespace = 'public'::regnamespace) THEN
        GRANT EXECUTE ON FUNCTION public.rls_auto_enable() TO anon, authenticated;
    END IF;
END $$;

-- New objects created later in this schema don't silently become public.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON TABLES    FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM anon, authenticated, PUBLIC;

-- ----------------------------------------------------------------------------
-- Realtime
-- ----------------------------------------------------------------------------

DO $$
DECLARE
    t TEXT;
BEGIN
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        FOREACH t IN ARRAY ARRAY['crawling_jobs', 'crawling_tasks', 'crawl_job_log'] LOOP
            IF NOT EXISTS (
                SELECT 1 FROM pg_publication_tables
                WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = t
            ) THEN
                EXECUTE format('ALTER PUBLICATION supabase_realtime ADD TABLE public.%I', t);
            END IF;
        END LOOP;
    END IF;
END $$;
