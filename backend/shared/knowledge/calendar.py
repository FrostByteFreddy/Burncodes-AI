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
