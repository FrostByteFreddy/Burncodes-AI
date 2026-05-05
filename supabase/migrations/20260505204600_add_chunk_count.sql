-- Add chunk_count to tenant_sources to track how many knowledge fragments were indexed per source
ALTER TABLE tenant_sources ADD COLUMN IF NOT EXISTS chunk_count INTEGER NOT NULL DEFAULT 0;
