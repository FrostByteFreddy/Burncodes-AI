-- Migration: rename indexing_mode values to 3-mode crawl_mode system
-- Replaces the boolean-style 'llm'/'fast' with three explicit crawl modes:
--   'soup'           — httpx fetch + trafilatura extraction, no Playwright, no LLM
--   'playwright'     — Crawl4AI + Playwright, heuristic chunking, no LLM
--   'playwright_llm' — Crawl4AI + Playwright + LLM cleaning (default, previous behaviour)
--
-- The old 'llm' value maps to 'playwright_llm', 'fast' maps to 'playwright'.

-- 1. Rename the column for clarity
ALTER TABLE tenants RENAME COLUMN indexing_mode TO crawl_mode;

-- 2. Migrate existing values
UPDATE tenants SET crawl_mode = 'playwright_llm' WHERE crawl_mode = 'llm';
UPDATE tenants SET crawl_mode = 'playwright'     WHERE crawl_mode = 'fast';

-- 3. Set correct default
ALTER TABLE tenants ALTER COLUMN crawl_mode SET DEFAULT 'playwright_llm';
