-- Enable Supabase Realtime for crawl tracking tables
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor → New Query)

alter publication supabase_realtime add table crawling_jobs;
alter publication supabase_realtime add table crawling_tasks;
