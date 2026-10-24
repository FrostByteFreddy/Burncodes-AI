-- ============================================================================
-- Server-side aggregation for /billing/usage and /chat/<tenant>/conversations.
--
-- Both endpoints used to fetch every row and sum in Python. PostgREST caps
-- responses at 1000 rows by default, so totals were silently truncated once a
-- user had more than 1000 chat messages or sources.
-- ============================================================================

-- One row per conversation, newest first.
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
        MAX(cl.created_at)                                  AS last_active,
        COUNT(*)::BIGINT                                    AS message_count,
        COALESCE(SUM(cl.cost_chf), 0)                       AS total_cost,
        (ARRAY_AGG(cl.user_message ORDER BY cl.created_at))[1] AS first_message
    FROM public.chat_logs cl
    WHERE cl.tenant_id = p_tenant_id
    GROUP BY cl.conversation_id
    ORDER BY last_active DESC;
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

-- Backend (service role) only; ownership is enforced in the API.
REVOKE EXECUTE ON FUNCTION public.conversation_summaries(UUID) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.usage_totals(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.conversation_summaries(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION public.usage_totals(UUID) TO service_role;

-- analytics_time_buckets reads chat_logs for any tenant id; same treatment.
REVOKE EXECUTE ON FUNCTION public.analytics_time_buckets(UUID, TIMESTAMPTZ, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.analytics_time_buckets(UUID, TIMESTAMPTZ, TEXT) TO service_role;
