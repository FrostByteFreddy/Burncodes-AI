"""
shared/knowledge/calendar.py

Calendar feeds (.ics) built on request from validated dates (tenant_events).
Residents subscribe to a feed's address; their calendar app re-fetches it
by itself, so new or moved dates reach everyone without anyone doing a thing.

Every entry keeps the same UID across fetches (hash of chatbot, series, zone
and date) so calendar apps update entries instead of duplicating them.
"""
import hashlib
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def calendar_key(series: str, zone: str) -> str:
    """Address part for one series/zone, e.g. "hauskehricht--zone-1".

    Keep in sync with worker_chat/app/chat/tasks.py (_calendar_key).
    """
    return slug(series) + (f"--{slug(zone)}" if zone else "")


_QUOTES = str.maketrans({c: '"' for c in "„“”«»‹›‚‘’'"})


def _norm(text: str | None) -> str:
    text = unicodedata.normalize("NFKC", text or "").translate(_QUOTES)
    return " ".join(text.split()).casefold()


def event_key(e: dict) -> tuple[str, str, str]:
    """Same name, same zone, same day: one date, whichever page it was read from."""
    return _norm(e.get("series")), _norm(e.get("zone")), str(e.get("event_date") or "")[:10]


def dedupe_events(rows: list[dict], rank=None) -> list[dict]:
    """
    Dates are stored per page, so an event shown on the home page, the event
    list and its own page is stored three times (and has to be: re-learning or
    removing one page must not take the others' dates with it). Readers merge
    them here. Keeps the order of `rows`; of each group the row whose source
    ranks highest (rank(row) -> number) is kept; an exception on any copy marks
    the date as exception, and the longest note wins.
    """
    best: dict[tuple, dict] = {}
    order: list[tuple] = []
    for r in rows:
        key = event_key(r)
        kept = best.get(key)
        if kept is None:
            best[key] = dict(r)
            order.append(key)
            continue
        if rank is not None and rank(r) > rank(kept):
            merged = dict(r)
            merged["is_exception"] = bool(r.get("is_exception") or kept.get("is_exception"))
            merged["notes"] = max((r.get("notes") or "", kept.get("notes") or ""), key=len)
            best[key] = merged
        else:
            kept["is_exception"] = bool(kept.get("is_exception") or r.get("is_exception"))
            if len(r.get("notes") or "") > len(kept.get("notes") or ""):
                kept["notes"] = r["notes"]
    return [best[k] for k in order]


def source_rank(event: dict, source: dict | None) -> int:
    """Which page to name for a date: its own page (title names it) > any specific page > the home page."""
    if not source:
        return 0
    url = source.get("source_location") or source.get("url") or ""
    path = url.split("://", 1)[-1].partition("/")[2].strip("/")
    named = bool(event.get("series")) and _norm(event["series"]) in _norm(source.get("title"))
    return 2 * named + bool(path)


def _escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    """RFC 5545: lines longer than 75 octets continue on the next line after a space."""
    raw = line.encode()
    if len(raw) <= 75:
        return line
    parts, current = [], b""
    for ch in line:
        b = ch.encode()
        if len(current) + len(b) > (75 if not parts else 74):
            parts.append(current.decode())
            current = b""
        current += b
    parts.append(current.decode())
    return "\r\n ".join(parts)


def build_ics(*, tenant_id: str, title: str, description: str, events: list[dict], sources: dict, now: datetime | None = None) -> str:
    """
    events: tenant_events rows (series, zone, event_date, is_exception, notes, source_id).
    sources: source_id -> {"title", "url"} for "where this comes from".
    """
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BurnCodes AI//Calendar feeds//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(title)}",
        f"X-WR-CALDESC:{_escape(description)}",
        # how often apps should check again (Apple/Outlook honour these; Google picks its own pace)
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H",
    ]
    for e in events:
        day = date.fromisoformat(e["event_date"])
        label = f"{e['series']} ({e['zone']})" if e.get("zone") else e["series"]
        uid = hashlib.sha1(f"{tenant_id}|{e['series']}|{e.get('zone') or ''}|{day.isoformat()}".encode()).hexdigest()
        notes = [n for n in [e.get("notes")] if n]
        if e.get("is_exception"):
            notes.insert(0, "Moved date")
        source = sources.get(e.get("source_id"))
        if source:
            notes.append(f"Source: {source['title']} {source['url']}".strip())
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}@burncodes-ai",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(day + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{_escape(label)}",
            *([f"DESCRIPTION:{_escape(chr(10).join(notes))}"] if notes else []),
            "TRANSP:TRANSPARENT",
            # reminder at 18:00 the evening before (all-day events start at midnight)
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_escape(label)}",
            "TRIGGER:-PT6H",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
