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
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

from celery import current_app as celery_app

from app.ai_models import DEFAULT_LEARNING_MODEL, LEARNING_MODELS, learning_model_key, learning_rates
from app.database.supabase_client import fetch_all, supabase
from app.logging_config import error_logger
from app.models.database import CrawlingStatus

LEARN_TASK = "app.data_processing.tasks.learn_source_task"
SCAN_TASK = "app.data_processing.tasks.crawl_tasks.process_single_url_task"
# a learn task that says "processing" for this long has died with its worker
STALE_LEARN_MINUTES = 20
START_LEARNING_TASK = "app.data_processing.tasks.start_learning_task"

# Removed pages are deleted after this many crawls without seeing them
MISSED_CRAWLS_BEFORE_REMOVAL = 2
# Scheduled re-crawls start learning on their own only below this estimate
AUTO_CONFIRM_MAX_CHF = float(os.getenv("RECRAWL_AUTO_CONFIRM_MAX_CHF", "5"))

# Documents longer than this are not read by Gemini page by page: their text
# is split into sections and made searchable only (no facts or dates).
# Important documents for residents are rarely longer.
MAX_LLM_PAGES = int(os.getenv("INDEXING_MAX_PAGES", "20"))
# Gemini can't answer longer than this per document (understanding.py)
_MAX_OUT = int(os.getenv("INDEXING_MAX_OUTPUT_TOKENS", "32000"))

# Token model for the estimate. Defaults until enough real learning runs are
# recorded (last_learn_*_tokens); then the median of those is used instead.
_PROMPT_OVERHEAD = 2_000
_PDF_IN_PER_PAGE = 2_900
_PDF_OUT_PER_PAGE = 900          # text PDFs answer with line ranges, not re-typed text
_INDEX_TOKENS_PER_PAGE = 600     # text of a page, for "searchable only" documents
_PAGE_IN_PER_TOKEN = 1.3         # a page's text as Gemini reads it (numbered lines)
_CALIBRATION_MIN_SAMPLES = 10


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(job_id: int | None, tenant_id: str, event: str, **data) -> None:
    """
    Appends to the job's live activity log (crawl_job_log, pushed to the
    dashboard via Realtime). Events are codes + data; the frontend renders
    them in the user's language. Never raises — logging must not break a crawl.
    """
    if job_id is None:
        return
    try:
        supabase.table("crawl_job_log").insert(
            {"job_id": job_id, "tenant_id": str(tenant_id), "event": event, "data": data}
        ).execute()
    except Exception as e:
        error_logger.debug("crawl_job_log insert failed for job %s: %s", job_id, e)


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

    same = existing.get("content_hash") == content_hash or existing.get("pending_hash") == content_hash
    unchanged = same and existing.get("status") in ("COMPLETED", "SKIPPED")
    if unchanged:
        # Learned, or sorted out before: nothing to do while it doesn't change.
        if existing.get("status") == "COMPLETED":
            base.pop("content_markdown", None)
    else:
        base["status"] = "QUEUED"
        base["skip_reason"] = None
    row = supabase.table("tenant_sources").update(base).eq("id", existing["id"]).execute().data[0]
    return row, "unchanged" if unchanged else "changed"


def delete_source_documents(source: dict) -> bool:
    """Deletes every File Search document of a source (legacy single doc + sections). True if all are gone."""
    from app.gemini_store.service import GeminiStoreService

    names = list(source.get("gemini_document_names") or [])
    if source.get("gemini_document_name"):
        names.append(source["gemini_document_name"])
    gone = True
    for name in dict.fromkeys(names):
        try:
            gone = GeminiStoreService.delete_document(name) is not False and gone
        except Exception as e:
            error_logger.warning("Could not delete Gemini document %s: %s", name, e)
            gone = False
    return gone


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
    return fetch_all(lambda: (
        supabase.table("tenant_sources")
        .select("id, source_type, source_location, content_tokens, file_pages, status")
        .eq("last_job_id", job_id).eq("status", "QUEUED").order("id")
    ))


def is_index_only(src: dict) -> bool:
    return (src.get("file_pages") or 0) > MAX_LLM_PAGES


def _median(values: list[float]) -> float | None:
    values = sorted(v for v in values if v and v > 0)
    return values[len(values) // 2] if values else None


def calibration() -> dict:
    """
    Tokens learning really took, from recent runs, so the estimate is close to
    the bill. Fitted on sums (not a typical page): what matters is the total.

    Until enough runs are recorded: conservative defaults with a fixed prompt
    overhead per source. Once calibrated, the per-token / per-page rates already
    contain that overhead and the fixed parts drop to what the data shows; adding
    them on top made younity's estimate CHF 19.22 for a run that cost CHF 5.99.
    """
    rows = (
        supabase.table("tenant_sources")
        .select("file_pages, content_tokens, last_learn_in_tokens, last_learn_out_tokens")
        .eq("learn_mode", "full").not_.is_("last_learn_out_tokens", "null")
        .order("id", desc=True).limit(500).execute()
    ).data or []
    pdfs = [r for r in rows if r.get("file_pages")]
    pages = [r for r in rows if not r.get("file_pages") and r.get("content_tokens")]
    cal = {**calibration_defaults(), "samples": len(rows)}
    if len(pdfs) >= _CALIBRATION_MIN_SAMPLES:
        n_pages = sum(r["file_pages"] for r in pdfs)
        cal.update(pdf_in=sum(r["last_learn_in_tokens"] or 0 for r in pdfs) / n_pages,
                   pdf_out=sum(r["last_learn_out_tokens"] or 0 for r in pdfs) / n_pages,
                   pdf_base=0)
    if len(pages) >= _CALIBRATION_MIN_SAMPLES:
        tokens = sum(r["content_tokens"] for r in pages)
        read = sum(r["last_learn_in_tokens"] or 0 for r in pages) - _PAGE_IN_PER_TOKEN * tokens
        cal.update(page_in_base=max(0, read / len(pages)),
                   page_out=sum(r["last_learn_out_tokens"] or 0 for r in pages) / tokens,
                   page_out_base=0)
    return cal


def estimate_source(src: dict, cal: dict | None = None) -> tuple[int, int, int]:
    """(extraction_in, extraction_out, embedding_tokens) expected for learning one source."""
    cal = {**calibration_defaults(), **(cal or {})}
    pages = src.get("file_pages") or 0
    if pages and pages > MAX_LLM_PAGES:
        return (0, 0, _INDEX_TOKENS_PER_PAGE * pages)   # searchable only: embedding, no Gemini reading
    if pages:
        out = min(_MAX_OUT, int(cal["pdf_out"] * pages))
        return (int(cal["pdf_base"] + cal["pdf_in"] * pages), out, out)
    tokens = src.get("content_tokens") or 0
    out = min(_MAX_OUT, int(cal["page_out_base"] + tokens * cal["page_out"]))
    return (int(cal["page_in_base"] + tokens * _PAGE_IN_PER_TOKEN), out, int(tokens * 1.2))


def calibration_defaults() -> dict:
    """The estimate's rates before any run is recorded (conservative)."""
    return {"pdf_in": _PDF_IN_PER_PAGE, "pdf_out": _PDF_OUT_PER_PAGE, "pdf_base": _PROMPT_OVERHEAD,
            "page_in_base": _PROMPT_OVERHEAD, "page_out": 0.6, "page_out_base": 500}


def tokens_cost(ext_in: int, ext_out: int, embed: int, model: str | None = None) -> float:
    """What learning costs the customer for these token counts with this learning model, in CHF."""
    rate = learning_rates(model)
    return ext_in / 1e6 * rate["input"] + ext_out / 1e6 * rate["output"] + embed / 1e6 * rate["embed"]


def compute_estimate(job_id: int) -> dict:
    pending = _pending_sources(job_id)
    cal = calibration()
    tasks = fetch_all(lambda: supabase.table("crawling_tasks").select("outcome").eq("job_id", job_id).order("id"))
    outcomes: dict[str, int] = {}
    for t in tasks:
        key = t.get("outcome") or "unknown"
        outcomes[key] = outcomes.get(key, 0) + 1

    ext_in = ext_out = embed = 0
    index_only = 0
    for src in pending:
        i, o, e = estimate_source(src, cal)
        ext_in, ext_out, embed = ext_in + i, ext_out + o, embed + e
        index_only += is_index_only(src)

    # what the sorting step set aside, by reason (shown so it can be taken back in)
    skipped = fetch_all(lambda: (
        supabase.table("tenant_sources").select("skip_reason")
        .eq("last_job_id", job_id).eq("status", "SKIPPED").order("id")
    ))
    skipped_by_reason: dict[str, int] = {}
    for s in skipped:
        key = s.get("skip_reason") or "other"
        skipped_by_reason[key] = skipped_by_reason.get(key, 0) + 1
    # one price per learning model; the customer picks when confirming
    costs = {key: round(tokens_cost(ext_in, ext_out, embed, key), 2) for key in LEARNING_MODELS}
    return {
        "to_learn": len(pending),
        "pages": sum(1 for s in pending if not s.get("file_pages")),
        "files": sum(1 for s in pending if s.get("file_pages")),
        "index_only": index_only,
        "max_pages": MAX_LLM_PAGES,
        "skipped": len(skipped),
        "skipped_by_reason": skipped_by_reason,
        "calibration_samples": cal.get("samples", 0),
        "outcomes": outcomes,
        "tokens_in": ext_in,
        "tokens_out": ext_out,
        "costs": costs,
        "model": DEFAULT_LEARNING_MODEL,
        "cost_chf": costs[DEFAULT_LEARNING_MODEL],
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
    rows = fetch_all(lambda: (
        supabase.table("tenant_sources")
        .select("id, source_location, missed_crawls, last_job_id, gemini_document_name, gemini_document_names")
        .eq("tenant_id", job["tenant_id"]).in_("source_type", ["URL", "FILE_URL"])
        .like("source_location", f"%://{host}%").order("id")
    ))
    removed = 0
    for src in rows:
        if src.get("last_job_id") == job["id"]:
            continue
        misses = (src.get("missed_crawls") or 0) + 1
        if misses >= MISSED_CRAWLS_BEFORE_REMOVAL:
            # the row goes only once Gemini no longer has its documents; else the next run retries
            if delete_source_documents(src):
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
    from app.knowledge.selection import apply_rules
    from app.knowledge.triage import triage_job
    apply_rules(job)  # what the customer left out before stays out
    # the sorting step takes a minute on big sites; the dashboard shows it as running
    log_event(job_id, job["tenant_id"], "triage_start")
    sorted_out = triage_job(job)
    log_event(job_id, job["tenant_id"], "triage", skipped=sorted_out)
    from app.knowledge.selection import recommend
    estimate = compute_estimate(job_id)
    estimate["removed"] = removed
    estimate["recommendations"] = recommend(job)
    supabase.table("crawling_jobs").update({"estimate": estimate}).eq("id", job_id).execute()
    error_logger.info("Crawl job %s scanned: %s", job_id, estimate)
    log_event(job_id, job["tenant_id"], "scan_done", to_learn=estimate["to_learn"],
              cost_chf=estimate["cost_chf"], removed=removed, outcomes=estimate["outcomes"])

    # Scheduled re-crawls are pre-approved up to a cap and only while the
    # balance covers them; anything else waits for the user like a manual crawl.
    # (with the model the previous run of this website was learned with)
    model = learning_model_key(job.get("learning_model"))
    cost = estimate["costs"][model]
    auto = (job.get("auto_confirm") and cost <= AUTO_CONFIRM_MAX_CHF
            and _balance_covers(job["tenant_id"], cost))
    if auto or estimate["to_learn"] == 0:
        start_learning(job_id)


def _balance_covers(tenant_id: str, cost_chf: float) -> bool:
    """True if the chatbot's owner has paid enough for this learning. Fails closed."""
    try:
        from app.billing.services import BillingService
        owner = BillingService.get_tenant_owner(tenant_id)
        return bool(owner) and BillingService.check_balance(owner) >= max(cost_chf, 0.01)
    except Exception as e:
        error_logger.warning("balance check for tenant %s failed: %s", tenant_id, e)
        return False


def refresh_estimate(job_id: int) -> dict:
    """Recomputes the estimate after the user took sources back in or set them aside."""
    job = supabase.table("crawling_jobs").select("estimate").eq("id", job_id).limit(1).execute().data
    estimate = compute_estimate(job_id)
    previous = (job[0].get("estimate") or {}) if job else {}
    estimate["removed"] = previous.get("removed", 0)
    estimate["recommendations"] = previous.get("recommendations") or []
    supabase.table("crawling_jobs").update({"estimate": estimate}).eq("id", job_id).execute()
    return estimate


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
    if pending:
        log_event(job_id, moved[0]["tenant_id"], "learn_start", count=len(pending))
    if not pending:
        finish_job_if_learned(job_id)
    return True


def resume_job(job: dict) -> str | None:
    """
    Continues a stopped crawl where it stopped. Returns the phase it resumes
    ("learning", "scanning", "estimate") or None if there's nothing to resume.

    - Stopped while learning: sources not learned yet are queued again; what
      was learned stays and isn't paid for twice.
    - Stopped while scanning: pages found but not read yet are read.
    - Discarded after the scan: back to the estimate.
    """
    job_id, tenant_id = job["id"], job["tenant_id"]
    if job.get("status") != CrawlingStatus.FAILED.value:
        return None

    if job.get("confirmed_at"):
        stale = (datetime.now(timezone.utc) - timedelta(minutes=STALE_LEARN_MINUTES)).isoformat()
        supabase.table("tenant_sources").update({"status": "QUEUED"}) \
            .eq("last_job_id", job_id).eq("status", "PROCESSING").lt("learn_started_at", stale).execute()
        pending = _pending_sources(job_id)
        if not pending:
            return None
        moved = supabase.table("crawling_jobs").update({"status": CrawlingStatus.INDEXING.value}) \
            .eq("id", job_id).eq("status", CrawlingStatus.FAILED.value).execute().data
        if not moved:
            return None
        for src in pending:
            celery_app.send_task(LEARN_TASK, args=[src["id"], job_id], queue="fast")
        log_event(job_id, tenant_id, "resumed", phase="learning", count=len(pending))
        return "learning"

    # stopped while scanning: "Stop" marks waiting pages FAILED without a result,
    # pages picked up afterwards end as "cancelled"
    stopped = fetch_all(lambda: (
        supabase.table("crawling_tasks").select("id, parent_url, outcome")
        .eq("job_id", job_id).eq("status", CrawlingStatus.FAILED.value).order("id")
    ))
    stopped = [t for t in stopped if t.get("outcome") in (None, "cancelled")]
    if stopped:
        moved = supabase.table("crawling_jobs").update({"status": CrawlingStatus.IN_PROGRESS.value}) \
            .eq("id", job_id).eq("status", CrawlingStatus.FAILED.value).execute().data
        if not moved:
            return None
        ids = [t["id"] for t in stopped]
        for i in range(0, len(ids), 200):
            supabase.table("crawling_tasks").update({
                "status": CrawlingStatus.PENDING.value, "outcome": None, "attempts": 0, "enqueued_at": now_iso(),
            }).in_("id", ids[i:i + 200]).execute()
        for t in stopped:
            celery_app.send_task(SCAN_TASK, kwargs={"task_id": t["id"], "tenant_id": tenant_id,
                                                    "parent_url": t.get("parent_url")}, queue="heavy")
        log_event(job_id, tenant_id, "resumed", phase="scanning", count=len(stopped))
        return "scanning"

    if job.get("estimate"):
        moved = supabase.table("crawling_jobs").update({"status": CrawlingStatus.SCANNED.value}) \
            .eq("id", job_id).eq("status", CrawlingStatus.FAILED.value).execute().data
        if moved:
            log_event(job_id, tenant_id, "resumed", phase="estimate")
            return "estimate"
    return None


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
        # Older deployments' scheduler sets COMPLETED by id without a report
        # (it raced this code while both ran against one database). Finish
        # such jobs properly instead of leaving them without a report.
        moved = (
            supabase.table("crawling_jobs")
            .update({"finished_at": now_iso()})
            .eq("id", job_id).eq("status", CrawlingStatus.COMPLETED.value)
            .is_("finished_at", "null").is_("report", "null")
            .execute()
        ).data
    if not moved:
        return
    try:
        report = build_report(moved[0])
        supabase.table("crawling_jobs").update({"report": report}).eq("id", job_id).execute()
        error_logger.info("Crawl job %s completed: %s", job_id, report["counts"])
        log_event(job_id, moved[0]["tenant_id"], "job_done", learned=report["counts"].get("learned", 0),
                  cost_chf=report["cost_chf"], attention=len(report["attention"]))
    except Exception as e:
        error_logger.error("Report for crawl job %s failed: %s", job_id, e, exc_info=True)


def issues_of(warnings) -> list[dict]:
    """
    A source's warnings as {kind, subject, …}. Free-text warnings from before
    2026-10-25 (typos, layout, line numbers …) are left out: mostly noise, and
    a re-learn replaces them.
    """
    return [w for w in warnings or [] if isinstance(w, dict) and w.get("kind")]


def build_report(job: dict) -> dict:
    """Aggregates what the crawl found. Deterministic — no LLM call."""
    job_id = job["id"]
    estimate = job.get("estimate") or {}
    sources = fetch_all(lambda: (
        supabase.table("tenant_sources")
        .select("id, source_location, source_type, status, status_code, title, summary, page_type, importance, "
                "importance_reason, warnings, learned_job_id, last_learn_cost_chf")
        .eq("last_job_id", job_id).order("id")
    ))
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
        # ids go into the URL, so ask in chunks
        ids, events = [s["id"] for s in sources], []
        for i in range(0, len(ids), 200):
            events += fetch_all(lambda chunk=ids[i:i + 200]: (
                supabase.table("tenant_events").select("source_id, series, zone, event_date")
                .in_("source_id", chunk).order("id")
            ))
        grouped: dict[tuple, list[str]] = {}
        for e in events:
            grouped.setdefault((e["source_id"], e["series"], e["zone"]), []).append(e["event_date"])
        today = date.today().isoformat()
        for (source_id, series, zone), dates in sorted(grouped.items()):
            dates.sort()
            src = by_id.get(source_id, {"id": source_id, "source_location": ""})
            upcoming = [d for d in dates if d >= today]
            schedules.append({
                **ref(src), "series": series, "zone": zone, "count": len(dates),
                "first": dates[0], "last": dates[-1], "next": upcoming[0] if upcoming else None,
                "expired": not upcoming,
            })

    attention = []
    for s in sources:
        for w in issues_of(s.get("warnings")):
            attention.append({**ref(s), **w})
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
