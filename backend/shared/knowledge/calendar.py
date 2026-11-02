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


def parse_time(value) -> str | None:
    """"19:00", "19.30", "9 Uhr", "19:00:00" -> "HH:MM"; None when there is no real time."""
    m = re.match(r"^\s*(\d{1,2})(?:[:.h](\d{2}))?(?::\d{2})?(?:\s*(?:uhr|h))?\s*$", str(value or ""), re.I)
    if not m:
        return None
    hour, minute = int(m[1]), int(m[2] or 0)
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def event_times(e: dict) -> tuple[str | None, str | None]:
    """
    (start, end) of an event. Midnight is what a model writes for "no time", and
    nothing we show starts then, so it counts as no time. No start, no end.
    """
    start = parse_time(e.get("start_time"))
    if not start or start == "00:00":
        return None, None
    return start, parse_time(e.get("end_time"))


def time_label(e: dict) -> str:
    """ "19:00-21:00", "19:00" or "". """
    start, end = event_times(e)
    return f"{start}-{end}" if start and end else start or ""


def event_matches(e: dict, query: str) -> bool:
    """Every word of the search appears in the name, zone, notes or date (2026-11-05 or 5.11.2026)."""
    day = str(e.get("event_date") or "")[:10]
    y, m, d = (day.split("-") + ["", "", ""])[:3]
    swiss = f"{d}.{m}.{y} {d.lstrip('0')}.{m.lstrip('0')}.{y}"
    plain = lambda text: "".join(c for c in unicodedata.normalize("NFKD", _norm(text)) if not unicodedata.combining(c))
    text = plain(f"{e.get('series')} {e.get('zone')} {e.get('notes')} {day} {swiss}")
    return all(word in text for word in plain(query).split())


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
            if not event_times(merged)[0]:
                merged["start_time"], merged["end_time"] = kept.get("start_time"), kept.get("end_time")
            best[key] = merged
        else:
            kept["is_exception"] = bool(kept.get("is_exception") or r.get("is_exception"))
            if len(r.get("notes") or "") > len(kept.get("notes") or ""):
                kept["notes"] = r["notes"]
            if not event_times(kept)[0]:
                kept["start_time"], kept["end_time"] = r.get("start_time"), r.get("end_time")
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


TIMEZONE = "Europe/Zurich"
# Times are local as printed; calendar apps need the rules to place them
_VTIMEZONE = [
    "BEGIN:VTIMEZONE", f"TZID:{TIMEZONE}",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0200", "TZNAME:CEST",
    "DTSTART:19700329T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0100", "TZNAME:CET",
    "DTSTART:19701025T030000", "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD",
    "END:VTIMEZONE",
]


def _when(day: date, start: str | None, end: str | None) -> tuple[list[str], str]:
    """DTSTART/DTEND lines and the reminder: all-day, or at the printed time."""
    if not start:
        # all-day events start at midnight: 18:00 the evening before
        return [f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{(day + timedelta(days=1)).strftime('%Y%m%d')}"], "-PT6H"
    stamp = lambda d, t: f"{d.strftime('%Y%m%d')}T{t.replace(':', '')}00"
    lines = [f"DTSTART;TZID={TIMEZONE}:{stamp(day, start)}"]
    if end:  # no printed end: none invented. An end before the start runs past midnight.
        lines.append(f"DTEND;TZID={TIMEZONE}:{stamp(day + timedelta(days=1) if end <= start else day, end)}")
    return lines, "-PT1H"


def build_ics(*, tenant_id: str, title: str, description: str, events: list[dict], sources: dict, now: datetime | None = None) -> str:
    """
    events: tenant_events rows (series, zone, event_date, start_time, end_time, is_exception, notes, source_id).
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
    if any(event_times(e)[0] for e in events):
        lines += _VTIMEZONE
    for e in events:
        day = date.fromisoformat(e["event_date"])
        when, reminder = _when(day, *event_times(e))
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
            *when,
            f"SUMMARY:{_escape(label)}",
            *([f"DESCRIPTION:{_escape(chr(10).join(notes))}"] if notes else []),
            "TRANSP:TRANSPARENT",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_escape(label)}",
            f"TRIGGER:{reminder}",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
