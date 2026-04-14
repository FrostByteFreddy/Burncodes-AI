-- Add missing columns to crawling_jobs
ALTER TABLE public.crawling_jobs
  ADD COLUMN IF NOT EXISTS excluded_urls TEXT[] DEFAULT '{}'::text[];

-- Add missing columns to crawling_tasks
ALTER TABLE public.crawling_tasks
  ADD COLUMN IF NOT EXISTS parent_url TEXT;

-- Add missing columns to tenant_sources
ALTER TABLE public.tenant_sources
  ADD COLUMN IF NOT EXISTS readme TEXT,
  ADD COLUMN IF NOT EXISTS input_tokens INTEGER,
  ADD COLUMN IF NOT EXISTS output_tokens INTEGER,
  ADD COLUMN IF NOT EXISTS cost_chf DECIMAL(10, 6);

-- Add missing columns to tenant_fine_tune
ALTER TABLE public.tenant_fine_tune
  ADD COLUMN IF NOT EXISTS vector_id TEXT;
