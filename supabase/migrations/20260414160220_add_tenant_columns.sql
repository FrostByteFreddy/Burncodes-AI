ALTER TABLE public.tenants 
  ADD COLUMN doc_language TEXT,
  ADD COLUMN translation_target TEXT,
  ADD COLUMN widget_config JSONB DEFAULT '{}'::jsonb;
