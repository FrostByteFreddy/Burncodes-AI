-- Add QUEUED value to the source_status enum
ALTER TYPE public.source_status ADD VALUE IF NOT EXISTS 'QUEUED' BEFORE 'PROCESSING';
