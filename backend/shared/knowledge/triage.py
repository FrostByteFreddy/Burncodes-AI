"""
shared/knowledge/triage.py

Sorts out what isn't worth learning before the estimate is shown: old
budgets and annual accounts, past years' minutes, outdated announcements,
older versions of documents that exist in a newer one, internal/technical
files. One cheap Gemini call per chunk of the found list (titles, URLs, page
counts, first lines). It decides only from that list, so the decision is
visible in the estimate and every sorted-out item can be taken back in.

Not billed: it costs fractions of a cent and saves the expensive part.
"""
import json
import os

from google import genai
from google.genai import types

from app.ai_models import TRIAGE_GEMINI_MODEL
from app.database.supabase_client import fetch_all, supabase
from app.logging_config import error_logger

# Reasons are codes; the dashboard shows them in the user's language
REASONS = ("archive_finance", "old_minutes", "outdated", "older_version", "internal", "other")
# set aside by hand in the estimate (not offered to the model)
MANUAL = "manual"
CHUNK = 300
SNIPPET_CHARS = 160

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"], http_options={"timeout": 120_000})
    return _client


_SCHEMA = {
    "type": "object",
    "properties": {
        "skip": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "reason": {"type": "string", "enum": list(REASONS)}},
                "required": ["id", "reason"],
            },
        },
    },
    "required": ["skip"],
}

_INSTRUCTIONS = """You prepare the knowledge base of a chatbot on the website of {site}.
Residents ask it everyday questions: opening hours, contacts, fees, services, forms, rules,
collection dates, events, current projects. Learning each document costs money.

Below is the list of pages and documents found on the website. Return the ids of entries
the chatbot will very likely never need, with one reason each:
- archive_finance: budgets, annual accounts, financial plans of past years (keep the current year)
- old_minutes: minutes, protocols, council decisions older than about a year
- outdated: past events, expired announcements, documents for years before {last_year}
- older_version: an older edition of a document that also exists in a newer edition in this list
- internal: technical, internal or administrative files residents don't use
- other: anything else clearly useless for residents' questions

Keep everything a resident could plausibly ask about, everything current, and anything you
are unsure about. When in doubt, keep it. Today is {today}."""


def _line(s: dict) -> str:
    kind = "pdf" if s.get("file_pages") else ("file" if s["source_type"] != "URL" else "page")
    pages = f" | {s['file_pages']} pages" if s.get("file_pages") else ""
    snippet = " ".join((s.get("content_markdown") or "").split())[:SNIPPET_CHARS]
    title = (s.get("title") or "").strip()[:120]
    return f"{s['id']} | {kind}{pages} | {title} | {s['source_location']}" + (f" | {snippet}" if snippet else "")


def _ask(lines: list[str], site: str) -> list[dict]:
    from datetime import date
    today = date.today()
    prompt = _INSTRUCTIONS.format(site=site, today=today.isoformat(), last_year=today.year - 1)
    response = _get_client().models.generate_content(
        model=TRIAGE_GEMINI_MODEL,
        contents=[prompt, "ENTRIES (id | kind | title | url | first words):\n" + "\n".join(lines)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=_SCHEMA,
            temperature=0,
            max_output_tokens=16_000,
        ),
    )
    try:
        return json.loads(response.text or "").get("skip") or []
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []


def triage_job(job: dict) -> int:
    """
    Marks sources of this job not worth learning as SKIPPED (with a reason).
    Returns how many were sorted out. Never raises: if sorting fails,
    everything stays queued, as before.
    """
    try:
        queued = fetch_all(lambda: (
            supabase.table("tenant_sources")
            .select("id, source_type, source_location, title, file_pages, content_markdown")
            .eq("last_job_id", job["id"]).eq("status", "QUEUED").order("id")
        ))
        if len(queued) < 10:
            return 0  # a handful of pages: nothing worth sorting
        valid = {s["id"] for s in queued}
        site = job.get("start_url") or ""
        skipped = 0
        for i in range(0, len(queued), CHUNK):
            chunk = queued[i:i + CHUNK]
            try:
                decisions = _ask([_line(s) for s in chunk], site)
            except Exception as e:
                error_logger.warning("triage: chunk %d of job %s failed: %s", i // CHUNK, job["id"], e)
                continue
            by_reason: dict[str, list[int]] = {}
            for d in decisions:
                if isinstance(d, dict) and d.get("id") in valid and d.get("reason") in REASONS:
                    by_reason.setdefault(d["reason"], []).append(d["id"])
            for reason, ids in by_reason.items():
                for j in range(0, len(ids), 200):
                    supabase.table("tenant_sources").update({"status": "SKIPPED", "skip_reason": reason}) \
                        .in_("id", ids[j:j + 200]).eq("status", "QUEUED").execute()
                skipped += len(ids)
        error_logger.info("triage: job %s sorted out %d of %d sources", job["id"], skipped, len(queued))
        return skipped
    except Exception as e:
        error_logger.error("triage: job %s failed, nothing sorted out: %s", job.get("id"), e, exc_info=True)
        return 0
