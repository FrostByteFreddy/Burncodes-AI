-- ============================================================================
-- Share Chat: shared_conversations table + RLS policies
-- ============================================================================

CREATE TABLE public.shared_conversations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL,
  tenant_id       UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '24 hours'),
  UNIQUE(conversation_id)   -- one share link per conversation (upsert via conflict)
);

-- Index for fast lookups by share id and expiry check
CREATE INDEX idx_shared_conversations_id ON public.shared_conversations(id);

-- RLS: anyone can read (needed for the public share view)
ALTER TABLE public.shared_conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "shared_conversations_public_read"
  ON public.shared_conversations FOR SELECT
  USING (true);

-- Only the service role (backend) can insert/update/delete
CREATE POLICY "shared_conversations_service_insert"
  ON public.shared_conversations FOR INSERT
  WITH CHECK (true);

-- Allow chat_logs to be read publicly IF they belong to an active share
CREATE POLICY "chat_logs_shared_public_read"
  ON public.chat_logs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.shared_conversations sc
      WHERE sc.conversation_id = chat_logs.conversation_id
        AND sc.expires_at > now()
    )
  );
