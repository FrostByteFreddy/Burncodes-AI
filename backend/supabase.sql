-- ============================================================================
-- Database Setup Script
-- Run this once to set up the entire database schema
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA extensions;

-- ============================================================================
-- Create ENUM Types
-- ============================================================================

CREATE TYPE public.source_type AS ENUM ('URL', 'FILE');
CREATE TYPE public.source_status AS ENUM ('PROCESSING', 'COMPLETED', 'ERROR');
CREATE TYPE public.crawling_status AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED');

-- ============================================================================
-- Create Tables
-- ============================================================================

-- Tenants table (references auth.users directly)
CREATE TABLE public.tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  intro_message TEXT,
  system_persona TEXT,
  rag_prompt_template TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Tenant fine-tuning rules
CREATE TABLE public.tenant_fine_tune (
  id SERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  trigger TEXT NOT NULL,
  instruction TEXT NOT NULL
);

-- Tenant data sources
CREATE TABLE public.tenant_sources (
  id SERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  source_type public.source_type NOT NULL,
  source_location TEXT NOT NULL,
  status public.source_status NOT NULL DEFAULT 'PROCESSING',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Tenant knowledge base
CREATE TABLE public.tenant_knowledge (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  knowledge TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Application logs
CREATE TABLE public.app_logs (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  user_id UUID NULL REFERENCES auth.users(id) ON DELETE SET NULL,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  traceback TEXT NULL,
  path TEXT NULL,
  lineno INTEGER NULL
);

COMMENT ON TABLE public.app_logs IS 'Stores application error logs for debugging and monitoring.';

-- Crawling jobs
CREATE TABLE public.crawling_jobs (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  start_url TEXT NOT NULL,
  max_depth INTEGER NOT NULL,
  status public.crawling_status NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Crawling tasks
CREATE TABLE public.crawling_tasks (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  job_id BIGINT NOT NULL REFERENCES public.crawling_jobs(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  depth INTEGER NOT NULL,
  status public.crawling_status NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Chat logs
CREATE TABLE public.chat_logs (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  conversation_id UUID NOT NULL,
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  user_message TEXT NOT NULL,
  ai_message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- Create Indexes
-- ============================================================================

CREATE INDEX idx_crawling_tasks_job_id ON public.crawling_tasks(job_id);
CREATE INDEX idx_crawling_tasks_status ON public.crawling_tasks(status);
CREATE INDEX idx_crawling_jobs_status ON public.crawling_jobs(status);
CREATE INDEX idx_chat_logs_tenant_conversation ON public.chat_logs(tenant_id, conversation_id, created_at);

-- ============================================================================
-- Enable Row Level Security (RLS)
-- ============================================================================

ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_fine_tune ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Create RLS Policies
-- ============================================================================

-- Policies for 'tenants' table
CREATE POLICY "Allow users to view their own tenants"
ON public.tenants FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Allow users to create their own tenants"
ON public.tenants FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow users to update their own tenants"
ON public.tenants FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Allow users to delete their own tenants"
ON public.tenants FOR DELETE
USING (auth.uid() = user_id);

-- Policies for 'tenant_fine_tune' table
CREATE POLICY "Allow users to manage fine_tune rules for their tenants"
ON public.tenant_fine_tune FOR ALL
USING (
  auth.uid() = (
    SELECT user_id FROM public.tenants WHERE id = tenant_id
  )
);

-- Policies for 'tenant_sources' table
CREATE POLICY "Allow users to manage sources for their tenants"
ON public.tenant_sources FOR ALL
USING (
  auth.uid() = (
    SELECT user_id FROM public.tenants WHERE id = tenant_id
  )
);

-- Policies for 'tenant_knowledge' table
CREATE POLICY "Users can manage knowledge for their own tenants"
ON public.tenant_knowledge FOR ALL
USING (
  auth.uid() = (
    SELECT user_id FROM public.tenants WHERE id = tenant_id
  )
);

-- Policies for 'chat_logs' table
CREATE POLICY "Allow tenant owner to read their own logs"
ON public.chat_logs FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.tenants
    WHERE tenants.id = chat_logs.tenant_id
    AND tenants.user_id = auth.uid()
  )
);

-- ============================================================================
-- Create Functions
-- ============================================================================

-- Function to get chat analytics
CREATE OR REPLACE FUNCTION public.get_chat_analytics(
  p_tenant_id UUID,
  p_timeframe_hours INT
)
RETURNS TABLE(
  time_bucket TIMESTAMPTZ,
  chat_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    time_bucket(
      CASE
        WHEN p_timeframe_hours > 24 THEN '1 day'
        ELSE '1 hour'
      END::INTERVAL,
      created_at
    ) AS time_bucket,
    COUNT(*) AS chat_count
  FROM
    public.chat_logs
  WHERE
    tenant_id = p_tenant_id
    AND created_at >= NOW() - (p_timeframe_hours || ' hours')::INTERVAL
  GROUP BY
    time_bucket
  ORDER BY
    time_bucket;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Setup Complete
-- ============================================================================