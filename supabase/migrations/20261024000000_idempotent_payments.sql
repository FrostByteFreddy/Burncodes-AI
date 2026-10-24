-- ============================================================================
-- Idempotent Stripe crediting
--
-- Every credit is keyed by the Stripe object that paid for it
-- ("checkout:<session id>" or "invoice:<invoice id>"). apply_payment() inserts
-- the key and credits the balance in one transaction, and does nothing if the
-- key was already processed. This stops the webhook + success-redirect double
-- credit and replays of /billing/verify-session.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.processed_payments (
    source_id  TEXT PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount_chf DECIMAL(10, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Service role only: RLS on, no policies.
ALTER TABLE public.processed_payments ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS processed_payments_user_id_idx
    ON public.processed_payments (user_id);

-- Returns TRUE if this call credited the balance, FALSE if already processed.
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

-- Balance-mutating RPCs are for the backend (service role) only. They are
-- SECURITY INVOKER so RLS already blocks writes from anon/authenticated, but
-- don't expose them through PostgREST at all.
REVOKE EXECUTE ON FUNCTION public.apply_payment(TEXT, UUID, DECIMAL) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.credit_balance(UUID, DECIMAL) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.deduct_balance(UUID, DECIMAL) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.apply_payment(TEXT, UUID, DECIMAL) TO service_role;
GRANT EXECUTE ON FUNCTION public.credit_balance(UUID, DECIMAL) TO service_role;
GRANT EXECUTE ON FUNCTION public.deduct_balance(UUID, DECIMAL) TO service_role;
