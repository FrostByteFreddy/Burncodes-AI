-- Migration: add indexing_mode to tenants
-- Adds a per-tenant setting that controls how ingested content is chunked.
--   'llm'  (default) — LLM-cleaned semantic chunks, billed to the tenant
--   'fast'           — RecursiveCharacterTextSplitter, no LLM, zero cost

ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS indexing_mode text NOT NULL DEFAULT 'llm';
