"""
shared/knowledge/learn.py

Learning one source (worker_fast): Gemini understanding → validation →
File Search indexing → facts/dates → billing.

Order matters: Gemini reads first (no side effects), the new sections are
indexed next, and only then are the old documents deleted — a failure halfway
leaves the previously indexed knowledge intact.
"""
import mimetypes
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from google.genai import errors as genai_errors

from app.billing.services import BillingService
from app.database.supabase_client import supabase
from app.gemini_store.service import GeminiStoreService
from app.knowledge import jobs
from app.ai_models import count_tokens
from app.knowledge.markdown import estimate_tokens, normalize_markdown, pdf_text
from app.knowledge.pdf_crosscheck import crosscheck_schedules
from app.knowledge.understanding import (
    WEEKDAYS,
    UnderstandingFailed,
    clean_warnings,
    log_summary,
    section_documents,
    understand_file,
    understand_markdown,
    validate_schedule,
)
from app.logging_config import error_logger
from app.security.url_guard import safe_client

MAX_FILE_BYTES = 50 * 1024 * 1024
_UPLOAD_THREADS = 4
_BOT_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SwiftAnswerBot/1.0; +https://ai.burn.codes)"}

# Formats Gemini reads natively (visually); others are converted to text first
_VISUAL_MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif",
}
_TEXT_EXT = {".txt", ".md", ".csv"}
_DOCX_EXT = {".docx"}


def _ext(location: str) -> str:
    return Path(urlparse(location).path or location).suffix.lower()


def load_file(source: dict) -> bytes:
    """Bytes of a FILE (uploaded, on local disk) or FILE_URL (re-downloaded) source."""
    location = source["source_location"]
    if source["source_type"] == "FILE":
        with open(location, "rb") as f:
            return f.read(MAX_FILE_BYTES + 1)
    with safe_client(follow_redirects=True, timeout=60.0, headers=_BOT_HEADERS) as client:
        resp = client.get(location)
    resp.raise_for_status()
    return resp.content


_INDEX_SECTION_PAGES = 2   # pages per section for documents made searchable only


def index_only_result(source: dict, data: bytes) -> dict:
    """
    Long documents: the PDF's own text, split into sections of a few pages,
    without Gemini reading it. Searchable in the chat, but no facts or dates.
    """
    text = pdf_text(data)
    if not text:
        raise UnderstandingFailed(f"scanned document over {jobs.MAX_LLM_PAGES} pages without a text layer")
    pages = [p for p in text.split("--- Seite ") if p.strip()]
    title = (source.get("title") or Path(urlparse(source["source_location"]).path).stem).replace("_", " ")
    sections = []
    for i in range(0, len(pages), _INDEX_SECTION_PAGES):
        chunk = pages[i:i + _INDEX_SECTION_PAGES]
        first = chunk[0].split(" ---", 1)[0].strip()
        last = chunk[-1].split(" ---", 1)[0].strip()
        body = "\n\n".join("Seite " + p.strip() for p in chunk)
        sections.append({"heading": f"Seiten {first}–{last}" if first != last else f"Seite {first}", "text": body})
    return {
        "title": title, "summary": "", "page_type": "document", "importance": 20,
        "importance_reason": f"Langes Dokument (über {jobs.MAX_LLM_PAGES} Seiten): nur durchsuchbar.",
        "sections": sections, "facts": [], "schedules": [], "single_events": [], "warnings": [],
    }


def understand_source(source: dict) -> tuple[dict, int, int]:
    """Runs Gemini on a source. Returns (result, input_tokens, output_tokens)."""
    location = source["source_location"]
    if source["source_type"] == "URL":
        return understand_markdown(source.get("content_markdown") or "", location)

    ext = _ext(location)
    data = load_file(source)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"file larger than {MAX_FILE_BYTES // (1024 * 1024)} MB")
    if ext == ".pdf" and jobs.is_index_only(source):
        return index_only_result(source, data), 0, 0
    if ext in _VISUAL_MIME:
        text_layer = pdf_text(data) if ext == ".pdf" else None
        result, i, o = understand_file(data, _VISUAL_MIME[ext], location, text_layer=text_layer)
        if ext == ".pdf" and result.get("schedules"):
            result["_crosscheck"] = crosscheck_schedules(data, result["schedules"])
        return result, i, o
    if ext in _DOCX_EXT:
        import io
        import docx2txt
        text = docx2txt.process(io.BytesIO(data))
        return understand_markdown(normalize_markdown(text), location)
    if ext in _TEXT_EXT:
        return understand_markdown(normalize_markdown(data.decode("utf-8", errors="replace")), location)
    guessed = mimetypes.guess_type(location)[0] or ""
    if guessed.startswith("text/"):
        return understand_markdown(normalize_markdown(data.decode("utf-8", errors="replace")), location)
    raise UnsupportedSource(ext or guessed or "unknown")


class UnsupportedSource(Exception):
    pass


# Share of a grid series' dates that may be missing from the PDF before the
# whole series is considered misread (below that, only those dates are dropped)
_MAX_MISSING_SHARE = 0.2


def _fmt(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%d.%m.%Y")
    except ValueError:
        return iso


def _validate(result: dict) -> None:
    """
    Decides which extracted dates are trustworthy.

    Grid PDFs (crosscheck available): a date must be printed in its month
    column; up to 20 % missing dates are dropped individually, more means the
    series was misread. Exceptions follow from the printed weekday.
    Everything else: the weekday rule (an off-weekday date must have been
    marked as exception by the model) — any problem rejects the series.
    """
    crosscheck = result.pop("_crosscheck", None)
    # warnings are {kind, subject, …}; the dashboard words them in the user's language
    warnings = clean_warnings(result)
    for i, series in enumerate(result.get("schedules") or []):
        label = " ".join(p for p in (series.get("name"), series.get("zone")) if p)
        problems = validate_schedule(series)
        grid_checked = crosscheck is not None and i in crosscheck
        missing = crosscheck.get(i, []) if grid_checked else []

        if missing:
            share = len(missing) / max(1, len(series.get("dates") or []))
            if share > _MAX_MISSING_SHARE:
                series["_problems"] = [f"{len(missing)} dates not printed in the grid"]
            else:
                series["dates"] = [d for d in series["dates"] if d.get("date", "")[:10] not in missing]
                warnings.append({"kind": "dates_dropped", "subject": label, "n": len(missing),
                                 "dates": [_fmt(d) for d in missing[:5]]})

        if grid_checked:
            # Printed in the grid → real. Only structural problems matter now.
            problems = [p for p in problems if "unparseable" in p]
        if problems and not series.get("_problems"):
            series["_problems"] = problems
        if series.get("_problems"):
            warnings.append({"kind": "dates_rejected", "subject": label})
            error_logger.warning("schedule %r rejected: %s", label, series["_problems"][:5])
            continue

        # Exceptions follow from the weekday whenever the series has one
        weekday = WEEKDAYS.get((series.get("regular_weekday") or "").strip().lower())
        seen = set()
        kept = []
        for d in series.get("dates") or []:
            iso = _parse_date(d.get("date", ""))
            if not iso or iso in seen:
                continue
            seen.add(iso)
            d["date"] = iso
            if weekday is not None:
                d["is_exception"] = date.fromisoformat(iso).weekday() != weekday
            kept.append(d)
        series["dates"] = kept
    result["warnings"] = warnings


def _parse_date(value: str) -> str | None:
    try:
        return date.fromisoformat((value or "").strip()[:10]).isoformat()
    except ValueError:
        return None


def _store_facts_and_events(tenant_id: str, source_id: int, result: dict) -> None:
    supabase.table("tenant_facts").delete().eq("source_id", source_id).execute()
    supabase.table("tenant_events").delete().eq("source_id", source_id).execute()

    facts = [
        {
            "tenant_id": tenant_id, "source_id": source_id,
            "kind": f.get("kind") or "other", "label": f.get("label") or "", "value": f.get("value") or "",
            "valid_from": _parse_date(f.get("valid_from", "")), "valid_to": _parse_date(f.get("valid_to", "")),
        }
        for f in result.get("facts") or [] if f.get("value")
    ]
    if facts:
        supabase.table("tenant_facts").insert(facts).execute()

    events = []
    for series in result.get("schedules") or []:
        if series.get("_problems"):
            continue
        for d in series.get("dates") or []:
            iso = _parse_date(d.get("date", ""))
            if iso:
                events.append({
                    "tenant_id": tenant_id, "source_id": source_id,
                    "series": series.get("name") or "", "zone": series.get("zone") or "",
                    "event_date": iso, "is_exception": bool(d.get("is_exception")),
                    "notes": series.get("notes") or "",
                })
    for e in result.get("single_events") or []:
        for d in e.get("dates") or []:
            iso = _parse_date(d)
            if iso:
                events.append({
                    "tenant_id": tenant_id, "source_id": source_id, "series": e.get("name") or "",
                    "zone": "", "event_date": iso, "is_exception": False, "notes": e.get("notes") or "",
                })
    for i in range(0, len(events), 500):
        supabase.table("tenant_events").insert(events[i:i + 500]).execute()


def _index(tenant_id: str, source: dict, result: dict) -> tuple[list[str], int]:
    """Uploads one document per section (+ facts/dates). Returns (document names, embedded tokens)."""
    docs = section_documents(result, source["source_location"])
    if not docs:
        return [], 0
    store = GeminiStoreService.get_or_create_store(tenant_id)
    metadata = {"source_id": str(source["id"]), "source_url": source["source_location"]}

    def upload(doc: tuple[str, str]) -> str:
        name, text = doc
        for attempt in range(3):
            try:
                return GeminiStoreService.upload_text(store_name=store, text=text, display_name=name,
                                                      metadata=metadata, bill=False)
            except genai_errors.ClientError as e:
                # a store created moments ago can answer 404 for a few seconds
                if e.code != 404 or attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))

    with ThreadPoolExecutor(max_workers=_UPLOAD_THREADS) as pool:
        names = list(pool.map(upload, docs))
    texts = [text for _, text in docs]
    # exact embedding tokens; the estimate only if count_tokens can't be reached
    exact = count_tokens(texts)
    return names, exact if exact is not None else sum(estimate_tokens(t) for t in texts)


def learn_source(source_id: int, job_id: int | None = None) -> None:
    claimed = (
        supabase.table("tenant_sources").update({"status": "PROCESSING", "learn_started_at": jobs.now_iso()})
        .eq("id", source_id).eq("status", "QUEUED").execute()
    ).data
    if not claimed:
        return  # duplicate message or already handled
    source = claimed[0]
    tenant_id = source["tenant_id"]

    try:
        if job_id is not None:
            job = supabase.table("crawling_jobs").select("status").eq("id", job_id).limit(1).execute().data
            if not job or job[0]["status"] == "FAILED":
                supabase.table("tenant_sources").update({"status": "QUEUED"}).eq("id", source_id).execute()
                return
        if not BillingService.tenant_has_balance(tenant_id):
            supabase.table("tenant_sources").update({"status": "ERROR", "status_code": 402}).eq("id", source_id).execute()
            return

        jobs.log_event(job_id, tenant_id, "learn_source", url=source["source_location"],
                       title=source.get("title") or "", kind=source["source_type"])
        result, in_tok, out_tok = understand_source(source)
        log_summary(source["source_location"], result)
        _validate(result)

        new_names, embed_tokens = _index(tenant_id, source, result)
        jobs.delete_source_documents(source)
        _store_facts_and_events(tenant_id, source_id, result)

        owner = BillingService.get_tenant_owner(tenant_id)
        cost = 0.0
        if owner:
            cost += BillingService.deduct_cost(owner, "extraction", in_tok, out_tok)
            cost += BillingService.deduct_cost(owner, "indexing", embed_tokens, 0)

        supabase.table("tenant_sources").update({
            "status": "COMPLETED",
            "status_code": source.get("status_code") or 200,
            "content_hash": source.get("pending_hash"),
            "last_changed_at": jobs.now_iso(),
            "learned_job_id": job_id,
            "title": (result.get("title") or "")[:500],
            "summary": result.get("summary"),
            "page_type": result.get("page_type"),
            "importance": max(0, min(100, int(result.get("importance") or 0))),
            "importance_reason": result.get("importance_reason"),
            "warnings": result.get("warnings") or [],
            "gemini_document_names": new_names,
            "indexed_chunks": len(new_names),
            "gemini_document_name": None,
            "last_learn_cost_chf": round(cost, 6),
            "cost_chf": round(float(source.get("cost_chf") or 0) + cost, 6),
            "input_tokens": (source.get("input_tokens") or 0) + in_tok + embed_tokens,
            "output_tokens": (source.get("output_tokens") or 0) + out_tok,
            # for the estimate: what learning this source really took
            "learn_mode": "index_only" if jobs.is_index_only(source) else "full",
            "last_learn_in_tokens": in_tok,
            "last_learn_out_tokens": out_tok,
        }).eq("id", source_id).execute()
        jobs.log_event(
            job_id, tenant_id, "learned", url=source["source_location"], title=result.get("title") or "",
            sections=len(new_names), facts=len(result.get("facts") or []),
            dates=sum(len(s.get("dates") or []) for s in result.get("schedules") or [] if not s.get("_problems")),
            importance=result.get("importance"), cost_chf=round(cost, 4),
        )
    except UnderstandingFailed as e:
        error_logger.warning("Source %s not understood: %s", source_id, e)
        jobs.log_event(job_id, tenant_id, "learn_failed", url=source["source_location"], reason=str(e))
        supabase.table("tenant_sources").update({
            "status": "ERROR", "status_code": 422,
            "warnings": [{"kind": "unreadable", "subject": source.get("title") or ""}],
        }).eq("id", source_id).execute()
    except UnsupportedSource as e:
        supabase.table("tenant_sources").update({"status": "UNSUPPORTED"}).eq("id", source_id).execute()
        error_logger.info("Source %s unsupported for learning: %s", source_id, e)
    except Exception as e:
        error_logger.error("Learning source %s failed: %s", source_id, e, exc_info=True)
        jobs.log_event(job_id, tenant_id, "learn_failed", url=source["source_location"], reason=type(e).__name__)
        supabase.table("tenant_sources").update({"status": "ERROR"}).eq("id", source_id).execute()
    finally:
        if job_id is not None:
            jobs.finish_job_if_learned(job_id)
