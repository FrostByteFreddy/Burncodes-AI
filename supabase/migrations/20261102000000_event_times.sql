-- Event times: the clock time printed on a page, stored beside the date.
-- Safe to run more than once. Applied to production on 2026-11-02.

-- Local clock time as printed on the page; NULL = no time printed (all-day).
ALTER TABLE public.tenant_events ADD COLUMN IF NOT EXISTS start_time TIME;
ALTER TABLE public.tenant_events ADD COLUMN IF NOT EXISTS end_time TIME;

-- Stores a page's dates: new events are inserted, known ones gain the page.
-- p_rows: [{tenant_id, source_id, source_rank, series, zone, event_date, is_exception, notes, start_time, end_time}]
CREATE OR REPLACE FUNCTION public.upsert_events(p_rows JSONB)
RETURNS VOID AS $$
    INSERT INTO public.tenant_events AS t
           (tenant_id, source_id, source_ids, source_rank, series, zone, event_date, is_exception, notes, start_time, end_time)
    SELECT DISTINCT ON (r->>'tenant_id', public.event_key_of(r->>'series', r->>'zone'), (r->>'event_date')::date)
           (r->>'tenant_id')::uuid, (r->>'source_id')::int, ARRAY[(r->>'source_id')::int],
           coalesce((r->>'source_rank')::int, 0), coalesce(r->>'series', ''), coalesce(r->>'zone', ''),
           (r->>'event_date')::date, coalesce((r->>'is_exception')::boolean, false), coalesce(r->>'notes', ''),
           (r->>'start_time')::time, (r->>'end_time')::time
      FROM jsonb_array_elements(p_rows) r
    ON CONFLICT (tenant_id, event_key, event_date) DO UPDATE SET
        source_ids   = (SELECT array_agg(DISTINCT x) FROM unnest(t.source_ids || EXCLUDED.source_ids) x),
        source_id    = CASE WHEN EXCLUDED.source_rank > t.source_rank THEN EXCLUDED.source_id ELSE t.source_id END,
        source_rank  = GREATEST(t.source_rank, EXCLUDED.source_rank),
        is_exception = t.is_exception OR EXCLUDED.is_exception,
        notes        = CASE WHEN length(EXCLUDED.notes) > length(t.notes) THEN EXCLUDED.notes ELSE t.notes END,
        -- a start and its end stay a pair: the more specific page's, or whichever page has one
        end_time     = CASE WHEN EXCLUDED.start_time IS NOT NULL AND (t.start_time IS NULL OR EXCLUDED.source_rank > t.source_rank)
                            THEN EXCLUDED.end_time ELSE t.end_time END,
        start_time   = CASE WHEN EXCLUDED.start_time IS NOT NULL AND (t.start_time IS NULL OR EXCLUDED.source_rank > t.source_rank)
                            THEN EXCLUDED.start_time ELSE t.start_time END;
$$ LANGUAGE sql;
