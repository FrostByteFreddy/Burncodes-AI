-- Migration: Add Gemini File Search Store columns
-- Adds the two columns needed by the Gemini File Search RAG pipeline:
--   tenants.gemini_file_store_name  — the File Search Store resource name for each tenant
--   tenant_sources.gemini_document_name — the indexed document resource name (used for deletion)
-- Also adds the FILE_URL source type and UNSUPPORTED source status to their respective enums.

-- ---------------------------------------------------------------------------
-- 1. tenants: store the per-tenant File Search Store resource name
-- ---------------------------------------------------------------------------
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS gemini_file_store_name TEXT DEFAULT NULL;

COMMENT ON COLUMN tenants.gemini_file_store_name IS
  'Gemini File Search Store resource name (e.g. fileSearchStores/abc123). '
  'NULL until the tenant uploads their first source. Created lazily by GeminiStoreService.';

-- ---------------------------------------------------------------------------
-- 2. tenant_sources: store the indexed document resource name
-- ---------------------------------------------------------------------------
ALTER TABLE tenant_sources
  ADD COLUMN IF NOT EXISTS gemini_document_name TEXT DEFAULT NULL;

COMMENT ON COLUMN tenant_sources.gemini_document_name IS
  'Gemini File Search document resource name (e.g. fileSearchStores/abc123/documents/doc_xyz). '
  'Used to delete the specific document when the source is removed. '
  'NULL for sources that failed to index or pre-date this migration.';

-- ---------------------------------------------------------------------------
-- 3. source_type enum: add FILE_URL
--    FILE_URL = a file link (PDF, DOCX, image, etc.) discovered during a website crawl.
--    Displayed as a FILE in the UI with the filename extracted from the URL path.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_enum
    WHERE enumlabel = 'FILE_URL'
      AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'source_type')
  ) THEN
    ALTER TYPE source_type ADD VALUE 'FILE_URL';
  END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- 4. source_status enum: add UNSUPPORTED
--    UNSUPPORTED = file type not accepted by Gemini File Search (e.g. .xlsx, .pptx).
--    Surfaces a meaningful status instead of a generic ERROR.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_enum
    WHERE enumlabel = 'UNSUPPORTED'
      AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'source_status')
  ) THEN
    ALTER TYPE source_status ADD VALUE 'UNSUPPORTED';
  END IF;
END;
$$;
