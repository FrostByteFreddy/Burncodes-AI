-- ============================================================================
-- Cleanup Migration: Remove dead schema artifacts + add updated_at triggers
-- ============================================================================

-- 1. Drop dead table (replaced by ChromaDB as vector store)
DROP TABLE IF EXISTS public.tenant_knowledge;

-- 2. Drop legacy analytics function (superseded by analytics_time_buckets)
DROP FUNCTION IF EXISTS public.get_chat_analytics(UUID, INT);

-- 3. Auto-update updated_at on crawling_jobs and crawling_tasks
--    These columns existed since the initial schema but were never updated
--    by the backend on status changes — only the DB default was ever written.

CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_crawling_jobs_updated_at
  BEFORE UPDATE ON public.crawling_jobs
  FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

CREATE TRIGGER trg_crawling_tasks_updated_at
  BEFORE UPDATE ON public.crawling_tasks
  FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
