"""
shared/knowledge/understanding.py

One Gemini call per changed page or file (INDEXING_GEMINI_MODEL) that returns:
  - sections   — semantic chunks. For Markdown, Gemini returns line ranges and
                 we slice the text ourselves (no output tokens spent rewriting
                 the page). For PDFs/images Gemini returns the section text.
  - summary, page_type, importance (0–100) + reason
  - facts      — opening hours, fees, contacts, deadlines, ...
  - schedules  — recurring date series (e.g. Abfallkalender) as one date per
                 entry, plus single events; validated deterministically below
  - warnings   — e.g. "valid only for 2025", "zone assignment only shown on a map"
"""
import json
import os
from datetime import date

from google import genai
from google.genai import types

from app.ai_models import INDEXING_GEMINI_MODEL
from app.knowledge.markdown import number_lines, slice_lines
from app.logging_config import error_logger

# Per-call timeout (ms, google-genai unit). Long PDFs take a while.
_TIMEOUT_MS = int(os.getenv("INDEXING_GEMINI_TIMEOUT_MS", "240000"))

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"], http_options={"timeout": _TIMEOUT_MS})
    return _client


PAGE_TYPES = ["content", "overview", "news", "event", "contact", "legal", "form", "navigation", "other"]
FACT_KINDS = ["opening_hours", "fee", "contact", "address", "deadline", "rule", "other"]

_FACTS = {
    "type": "array",
    "description": "Concrete facts a visitor would ask about. Copy values exactly.",
    "items": {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": FACT_KINDS},
            "label": {"type": "string", "description": "What the fact is about, e.g. 'Öffnungszeiten Werkhof'"},
            "value": {"type": "string", "description": "The fact itself, verbatim where possible"},
            "valid_from": {"type": "string", "description": "ISO date if printed, else ''"},
            "valid_to": {"type": "string", "description": "ISO date if printed, else ''"},
        },
        "required": ["kind", "label", "value", "valid_from", "valid_to"],
    },
}
_SCHEDULES = {
    "type": "array",
    "description": "Recurring date series printed as a calendar, table or list (e.g. waste collection per zone). "
                   "Emit every date. Empty if the content has none.",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "e.g. 'Hauskehricht und Sperrgut'"},
            "zone": {"type": "string", "description": "Zone/area if the series is area-specific, else ''"},
            "regular_weekday": {"type": "string", "description": "Weekday printed for the series (in the document's language), else ''"},
            "notes": {"type": "string", "description": "Times, meeting points, conditions"},
            "dates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "ISO YYYY-MM-DD"},
                        "is_exception": {"type": "boolean", "description": "Marked as an exception (e.g. printed in red, footnote)"},
                    },
                    "required": ["date", "is_exception"],
                },
            },
        },
        "required": ["name", "zone", "regular_weekday", "notes", "dates"],
    },
}
_EVENTS = {
    "type": "array",
    "description": "One-off dated events (e.g. Christbaumabfuhr, Repair Café). Expand date ranges to every day.",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "dates": {"type": "array", "items": {"type": "string", "description": "ISO YYYY-MM-DD"}},
            "notes": {"type": "string"},
        },
        "required": ["name", "dates", "notes"],
    },
}


def _schema(sections_by_lines: bool) -> dict:
    if sections_by_lines:
        section = {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
            },
            "required": ["heading", "start_line", "end_line"],
        }
    else:
        section = {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "text": {"type": "string", "description": "Section content as Markdown, tables as Markdown tables, faithful to the document"},
            },
            "required": ["heading", "text"],
        }
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "language": {"type": "string", "description": "ISO 639-1"},
            "page_type": {"type": "string", "enum": PAGE_TYPES},
            "summary": {"type": "string", "description": "2–4 sentences, in the content's language"},
            "importance": {"type": "integer", "description": "0–100: how likely visitors need this to answer real questions"},
            "importance_reason": {"type": "string", "description": "One sentence, in the content's language"},
            "sections": {"type": "array", "items": section},
            "facts": _FACTS,
            "schedules": _SCHEDULES,
            "single_events": _EVENTS,
            "warnings": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Problems a site owner should know: outdated validity, information only in images/maps, "
                               "unreadable parts, contradictions. In the content's language. Empty if none.",
            },
        },
        "required": ["title", "language", "page_type", "summary", "importance", "importance_reason",
                     "sections", "facts", "schedules", "single_events", "warnings"],
    }


_INSTRUCTIONS = """You index content for a customer-service chatbot of an organisation (often a municipality).
Today is {today}. Source: {source}.

Tasks:
1. Split the content into coherent sections a visitor might ask about. {section_rule}
   Skip pure navigation, link lists and repeated boilerplate.
2. Summarise the content and rate its importance for answering visitors' questions
   (100 = essential everyday information such as collection dates, opening hours, fees, deadlines;
   0 = no useful information). Overview pages that only list links score low.
3. Extract facts and dates exactly as printed. Never invent or infer dates.
   For calendars read row by row: a date belongs to the row (series/zone) and column (month) it is printed in.
4. Add warnings for anything a site owner should fix or know (e.g. validity has ended before today).
Answer in the content's language."""


def _call(contents: list, schema: dict) -> tuple[dict, int, int]:
    response = _get_client().models.generate_content(
        model=INDEXING_GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema,
            temperature=0,
        ),
    )
    usage = getattr(response, "usage_metadata", None)
    in_tok = getattr(usage, "prompt_token_count", 0) or 0
    out_tok = getattr(usage, "candidates_token_count", 0) or 0
    return json.loads(response.text or "{}"), in_tok, out_tok


def understand_markdown(markdown: str, source: str, today: date | None = None) -> tuple[dict, int, int]:
    """Analyse page Markdown. Returns (result, input_tokens, output_tokens); sections carry 'text'."""
    today = today or date.today()
    prompt = _INSTRUCTIONS.format(
        today=today.isoformat(),
        source=source,
        section_rule="Return each section as a heading plus the line range (start_line/end_line, inclusive) "
                     "of the numbered content below. Ranges must not overlap.",
    )
    result, in_tok, out_tok = _call([prompt, "CONTENT:\n" + number_lines(markdown)], _schema(sections_by_lines=True))
    sections = []
    for s in result.get("sections") or []:
        text = slice_lines(markdown, s.get("start_line", 0), s.get("end_line", 0))
        if text:
            sections.append({"heading": s.get("heading", ""), "text": text})
    result["sections"] = sections
    return result, in_tok, out_tok


def understand_file(data: bytes, mime_type: str, source: str, today: date | None = None) -> tuple[dict, int, int]:
    """Analyse a PDF/image/document visually. Returns (result, input_tokens, output_tokens)."""
    today = today or date.today()
    prompt = _INSTRUCTIONS.format(
        today=today.isoformat(),
        source=source,
        section_rule="Return each section with its full content as Markdown (tables as Markdown tables).",
    )
    part = types.Part.from_bytes(data=data, mime_type=mime_type)
    return _call([part, prompt], _schema(sections_by_lines=False))


# ---------------------------------------------------------------------------
# Deterministic validation of extracted schedules
# ---------------------------------------------------------------------------

_WEEKDAYS = {
    # de / en / fr
    "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3, "freitag": 4, "samstag": 5, "sonntag": 6,
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
    "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4, "samedi": 5, "dimanche": 6,
}


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat((value or "").strip()[:10])
    except ValueError:
        return None


def validate_schedule(series: dict) -> list[str]:
    """
    Returns problems found in one extracted series (empty list = trustworthy):
    unparseable or duplicate dates, dates off the printed weekday that aren't
    marked as exceptions, and exceptions that fall on the regular weekday.
    """
    problems = []
    weekday = _WEEKDAYS.get((series.get("regular_weekday") or "").strip().lower())
    seen = set()
    for entry in series.get("dates") or []:
        d = _parse_date(entry.get("date", ""))
        if not d:
            problems.append(f"unparseable date {entry.get('date')!r}")
            continue
        if d in seen:
            problems.append(f"duplicate date {d.isoformat()}")
        seen.add(d)
        if weekday is None:
            continue
        exception = bool(entry.get("is_exception"))
        if d.weekday() != weekday and not exception:
            problems.append(f"{d.isoformat()} is not on the printed weekday and not marked as an exception")
        if d.weekday() == weekday and exception:
            problems.append(f"{d.isoformat()} is marked as an exception but falls on the regular weekday")
    return problems


def section_documents(result: dict, url: str) -> list[tuple[str, str]]:
    """
    Builds the (display_name, text) documents to index for one source. Each
    section carries the page title and summary as context so a chunk retrieved
    on its own still says what it belongs to. Facts and dates get their own
    document so they're retrievable by File Search as well.
    """
    title = (result.get("title") or url).strip()
    summary = (result.get("summary") or "").strip()
    docs = []
    for i, s in enumerate(result.get("sections") or [], start=1):
        heading = (s.get("heading") or "").strip()
        body = s.get("text", "").strip()
        if not body:
            continue
        text = f"# {title}\n## {heading}\nQuelle: {url}\nKontext: {summary}\n\n{body}"
        docs.append((f"{title} — {heading or i}"[:500], text))

    lines = []
    for f in result.get("facts") or []:
        validity = " – ".join(v for v in (f.get("valid_from"), f.get("valid_to")) if v)
        lines.append(f"- {f.get('label')}: {f.get('value')}" + (f" (gültig {validity})" if validity else ""))
    for s in result.get("schedules") or []:
        if s.get("_problems"):
            continue  # unvalidated dates are not indexed as facts
        label = " ".join(p for p in (s.get("name"), s.get("zone")) if p)
        dates = ", ".join(
            d["date"] + (" (Ausnahme)" if d.get("is_exception") else "") for d in s.get("dates") or []
        )
        lines.append(f"- {label}{' — ' + s['notes'] if s.get('notes') else ''}: {dates}")
    for e in result.get("single_events") or []:
        lines.append(f"- {e.get('name')}: {', '.join(e.get('dates') or [])}{' — ' + e['notes'] if e.get('notes') else ''}")
    if lines:
        docs.append((f"{title} — Fakten und Termine"[:500], f"# {title}\n## Fakten und Termine\nQuelle: {url}\n\n" + "\n".join(lines)))
    return docs


def log_summary(source: str, result: dict) -> None:
    error_logger.info(
        "understood %s: type=%s importance=%s sections=%d facts=%d schedules=%d events=%d warnings=%d",
        source, result.get("page_type"), result.get("importance"), len(result.get("sections") or []),
        len(result.get("facts") or []), len(result.get("schedules") or []),
        len(result.get("single_events") or []), len(result.get("warnings") or []),
    )
