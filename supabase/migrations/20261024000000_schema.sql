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

-- processed_payments and shared_conversations: no policies (service role only).

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
GRANT SELECT ON public.tenants, public.crawling_jobs, public.crawling_tasks TO authenticated;

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
        FOREACH t IN ARRAY ARRAY['crawling_jobs', 'crawling_tasks'] LOOP
            IF NOT EXISTS (
                SELECT 1 FROM pg_publication_tables
                WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = t
            ) THEN
                EXECUTE format('ALTER PUBLICATION supabase_realtime ADD TABLE public.%I', t);
            END IF;
        END LOOP;
    END IF;
END $$;
