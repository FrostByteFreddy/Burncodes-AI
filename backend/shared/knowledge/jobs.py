"""
shared/knowledge/jobs.py

Crawl job lifecycle, shared by worker_heavy (scan), worker_fast (learn,
scheduler) and the API (confirm):

    IN_PROGRESS  scan: fetch, convert, hash, compare — no LLM, not billed
    SCANNED      estimate stored; waits for the user to confirm
                 (scheduled re-crawls and jobs with nothing to learn skip this)
    INDEXING     Gemini reads every new/changed source (billed)
    COMPLETED    report stored on the job
    FAILED       cancelled or broken

State transitions are conditional UPDATEs (… WHERE status = X), so when
several workers finish at the same time exactly one performs the transition.
"""
import os
from datetime import date, datetime, timezone
from urllib.parse import urlparse

from celery import current_app as celery_app

from app.ai_models import RATES
from app.database.supabase_client import supabase
from app.logging_config import error_logger
from app.models.database import CrawlingStatus

LEARN_TASK = "app.data_processing.tasks.learn_source_task"
START_LEARNING_TASK = "app.data_processing.tasks.start_learning_task"

# Removed pages are deleted after this many crawls without seeing them
MISSED_CRAWLS_BEFORE_REMOVAL = 2
# Scheduled re-crawls start learning on their own only below this estimate
AUTO_CONFIRM_MAX_CHF = float(os.getenv("RECRAWL_AUTO_CONFIRM_MAX_CHF", "5"))

# Token model for the estimate, calibrated on real pages/PDFs with Gemini 4
# (Zofingen homepage: 730 Markdown tokens → ~3.0k in / 1.0k out;
#  2-page Abfallkalender PDF → ~7.7k in / 13k out).
_PROMPT_OVERHEAD = 2_000
_PDF_IN_PER_PAGE = 2_900
_PDF_OUT_PER_PAGE = 6_500


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Sources: one row per (tenant, location)
# ---------------------------------------------------------------------------

def get_source(tenant_id: str, location: str) -> dict | None:
    rows = (
        supabase.table("tenant_sources").select("*")
        .eq("tenant_id", tenant_id).eq("source_location", location)
        .order("id", desc=True).limit(1).execute()
    ).data
    return rows[0] if rows else None


def record_scan(
    tenant_id: str,
    location: str,
    source_type: str,
    job_id: int | None,
    content_hash: str,
    fields: dict,
) -> tuple[dict, str]:
    """
    Creates or updates the source for a scanned location.
    Returns (row, outcome) with outcome 'new' | 'changed' | 'unchanged'.
    The source is QUEUED for learning unless its content is already indexed.
    """
    existing = get_source(tenant_id, location)
    base = {
        **fields,
        "pending_hash": content_hash,
        "last_seen_at": now_iso(),
        "missed_crawls": 0,
        "last_job_id": job_id,
    }
    if existing is None:
        row = supabase.table("tenant_sources").insert({
            **base,
            "tenant_id": tenant_id,
            "source_location": location,
            "source_type": source_type,
            "status": "QUEUED",
        }).execute().data[0]
        return row, "new"

    unchanged = existing.get("content_hash") == content_hash and existing.get("status") == "COMPLETED"
    if unchanged:
        # Keep the stored Markdown; nothing to re-learn.
        base.pop("content_markdown", None)
    else:
        base["status"] = "QUEUED"
    row = supabase.table("tenant_sources").update(base).eq("id", existing["id"]).execute().data[0]
    return row, "unchanged" if unchanged else "changed"


def delete_source_documents(source: dict) -> None:
    """Deletes every File Search document of a source (legacy single doc + sections)."""
    from app.gemini_store.service import GeminiStoreService

    names = list(source.get("gemini_document_names") or [])
    if source.get("gemini_document_name"):
        names.append(source["gemini_document_name"])
    for name in dict.fromkeys(names):
        try:
            GeminiStoreService.delete_document(name)
        except Exception as e:
            error_logger.warning("Could not delete Gemini document %s: %s", name, e)


# ---------------------------------------------------------------------------
# Scan → estimate → confirm
# ---------------------------------------------------------------------------

def _outstanding_tasks(job_id: int) -> bool:
    rows = (
        supabase.table("crawling_tasks").select("id")
        .eq("job_id", job_id)
        .in_("status", [CrawlingStatus.PENDING.value, CrawlingStatus.IN_PROGRESS.value])
        .limit(1).execute()
    ).data
    return bool(rows)


def _pending_sources(job_id: int) -> list[dict]:
    return (
        supabase.table("tenant_sources")
        .select("id, source_type, source_location, content_tokens, file_pages, status")
        .eq("last_job_id", job_id).eq("status", "QUEUED")
        .limit(20000).execute()
    ).data or []


def estimate_source(src: dict) -> tuple[int, int, int]:
    """(extraction_in, extraction_out, embedding_tokens) expected for learning one source."""
    pages = src.get("file_pages") or 0
    if pages:
        return (_PROMPT_OVERHEAD + _PDF_IN_PER_PAGE * pages, _PDF_OUT_PER_PAGE * pages, _PDF_OUT_PER_PAGE * pages)
    tokens = src.get("content_tokens") or 0
    return (_PROMPT_OVERHEAD + int(tokens * 1.3), 500 + int(tokens * 0.6), int(tokens * 1.2))


def compute_estimate(job_id: int) -> dict:
    pending = _pending_sources(job_id)
    tasks = (
        supabase.table("crawling_tasks").select("outcome").eq("job_id", job_id).limit(20000).execute()
    ).data or []
    outcomes: dict[str, int] = {}
    for t in tasks:
        key = t.get("outcome") or "unknown"
        outcomes[key] = outcomes.get(key, 0) + 1

    ext_in = ext_out = embed = 0
    for src in pending:
        i, o, e = estimate_source(src)
        ext_in, ext_out, embed = ext_in + i, ext_out + o, embed + e
    cost = (
        ext_in / 1e6 * RATES["extraction"]["input"]
        + ext_out / 1e6 * RATES["extraction"]["output"]
        + embed / 1e6 * RATES["indexing"]["input"]
    )
    return {
        "to_learn": len(pending),
        "pages": sum(1 for s in pending if not s.get("file_pages")),
        "files": sum(1 for s in pending if s.get("file_pages")),
        "outcomes": outcomes,
        "tokens_in": ext_in,
        "tokens_out": ext_out,
        "cost_chf": round(cost, 2),
        "computed_at": now_iso(),
    }


def _mark_missed_sources(job: dict) -> int:
    """
    Full-site crawls: sources under the same host that this crawl didn't see
    count a miss; after MISSED_CRAWLS_BEFORE_REMOVAL misses they're removed
    (page deleted on the site). Returns the number removed now.
    """
    if job.get("single_page_only"):
        return 0
    host = urlparse(job["start_url"]).netloc
    if not host:
        return 0
    rows = (
        supabase.table("tenant_sources")
        .select("id, source_location, missed_crawls, last_job_id, gemini_document_name, gemini_document_names")
        .eq("tenant_id", job["tenant_id"]).in_("source_type", ["URL", "FILE_URL"])
        .like("source_location", f"%://{host}%")
        .limit(20000).execute()
    ).data or []
    removed = 0
    for src in rows:
        if src.get("last_job_id") == job["id"]:
            continue
        misses = (src.get("missed_crawls") or 0) + 1
        if misses >= MISSED_CRAWLS_BEFORE_REMOVAL:
            delete_source_documents(src)
            supabase.table("tenant_sources").delete().eq("id", src["id"]).execute()
            removed += 1
        else:
            supabase.table("tenant_sources").update({"missed_crawls": misses}).eq("id", src["id"]).execute()
    return removed


def complete_scan_if_done(job_id: int) -> None:
    """Called after every scan task. The last one moves the job to SCANNED/INDEXING."""
    if _outstanding_tasks(job_id):
        return
    moved = (
        supabase.table("crawling_jobs")
        .update({"status": CrawlingStatus.SCANNED.value})
        .eq("id", job_id).eq("status", CrawlingStatus.IN_PROGRESS.value)
        .execute()
    ).data
    if not moved:
        return  # another worker did it, or the job was cancelled
    job = moved[0]
    removed = _mark_missed_sources(job)
    estimate = compute_estimate(job_id)
    estimate["removed"] = removed
    supabase.table("crawling_jobs").update({"estimate": estimate}).eq("id", job_id).execute()
    error_logger.info("Crawl job %s scanned: %s", job_id, estimate)

    # Scheduled re-crawls are pre-approved up to a cap; anything pricier waits
    # for the user like a manual crawl.
    auto = job.get("auto_confirm") and estimate["cost_chf"] <= AUTO_CONFIRM_MAX_CHF
    if auto or estimate["to_learn"] == 0:
        start_learning(job_id)


def start_learning(job_id: int) -> bool:
    """SCANNED → INDEXING and queue a learn task per pending source. Returns False if not SCANNED."""
    moved = (
        supabase.table("crawling_jobs")
        .update({"status": CrawlingStatus.INDEXING.value, "confirmed_at": now_iso()})
        .eq("id", job_id).eq("status", CrawlingStatus.SCANNED.value)
        .execute()
    ).data
    if not moved:
        return False
    pending = _pending_sources(job_id)
    for src in pending:
        celery_app.send_task(LEARN_TASK, args=[src["id"], job_id], queue="fast")
    error_logger.info("Crawl job %s: learning %d source(s)", job_id, len(pending))
    if not pending:
        finish_job_if_learned(job_id)
    return True


# ---------------------------------------------------------------------------
# Learn → report
# ---------------------------------------------------------------------------

def finish_job_if_learned(job_id: int) -> None:
    left = (
        supabase.table("tenant_sources").select("id")
        .eq("last_job_id", job_id).in_("status", ["QUEUED", "PROCESSING"])
        .limit(1).execute()
    ).data
    if left:
        return
    moved = (
        supabase.table("crawling_jobs")
        .update({"status": CrawlingStatus.COMPLETED.value, "finished_at": now_iso()})
        .eq("id", job_id).eq("status", CrawlingStatus.INDEXING.value)
        .execute()
    ).data
    if not moved:
        return
    try:
        report = build_report(moved[0])
        supabase.table("crawling_jobs").update({"report": report}).eq("id", job_id).execute()
        error_logger.info("Crawl job %s completed: %s", job_id, report["counts"])
    except Exception as e:
        error_logger.error("Report for crawl job %s failed: %s", job_id, e, exc_info=True)


def build_report(job: dict) -> dict:
    """Aggregates what the crawl found. Deterministic — no LLM call."""
    job_id = job["id"]
    estimate = job.get("estimate") or {}
    sources = (
        supabase.table("tenant_sources")
        .select("id, source_location, source_type, status, status_code, title, summary, page_type, importance, "
                "importance_reason, warnings, learned_job_id, last_learn_cost_chf")
        .eq("last_job_id", job_id).limit(20000).execute()
    ).data or []
    learned = [s for s in sources if s.get("learned_job_id") == job_id]
    by_id = {s["id"]: s for s in sources}

    def ref(s: dict) -> dict:
        return {"source_id": s["id"], "title": s.get("title") or s["source_location"], "url": s["source_location"]}

    highlights = sorted(
        (s for s in sources if (s.get("importance") or 0) >= 60 and s.get("status") == "COMPLETED"),
        key=lambda s: -(s.get("importance") or 0),
    )[:12]

    schedules = []
    if sources:
        events = (
            supabase.table("tenant_events")
            .select("source_id, series, zone, event_date")
            .in_("source_id", [s["id"] for s in sources])
            .limit(20000).execute()
        ).data or []
        grouped: dict[tuple, list[str]] = {}
        for e in events:
            grouped.setdefault((e["source_id"], e["series"], e["zone"]), []).append(e["event_date"])
        today = date.today().isoformat()
        for (source_id, series, zone), dates in sorted(grouped.items()):
            dates.sort()
            src = by_id.get(source_id, {"id": source_id, "source_location": ""})
            schedules.append({
                **ref(src), "series": series, "zone": zone, "count": len(dates),
                "first": dates[0], "last": dates[-1], "expired": dates[-1] < today,
            })

    attention = []
    for s in sources:
        for w in s.get("warnings") or []:
            attention.append({**ref(s), "message": w})
    errors: dict[str, int] = {}
    for s in sources:
        if s.get("status") in ("ERROR", "UNSUPPORTED"):
            key = str(s.get("status_code") or s.get("status"))
            errors[key] = errors.get(key, 0) + 1

    return {
        "generated_at": now_iso(),
        "counts": {
            **(estimate.get("outcomes") or {}),
            "learned": len(learned),
            "removed": estimate.get("removed", 0),
            "errors": sum(errors.values()),
        },
        "cost_chf": round(sum(float(s.get("last_learn_cost_chf") or 0) for s in learned), 4),
        "highlights": [
            {**ref(s), "importance": s.get("importance"), "reason": s.get("importance_reason"),
             "page_type": s.get("page_type"), "summary": s.get("summary")}
            for s in highlights
        ],
        "schedules": schedules,
        "attention": attention[:50],
        "errors": errors,
    }
