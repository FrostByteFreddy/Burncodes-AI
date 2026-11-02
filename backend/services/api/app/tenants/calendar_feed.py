"""
Public calendar feeds for residents: GET /api/calendar/<tenant>/<keys>.ics

Calendar apps poll these themselves, many from the same few server IPs
(Google, Apple), so there's no per-IP limit; instead responses are cheap,
cached for a few minutes and answered with 304 when nothing changed.
A chatbot that is off, password-protected or has calendars disabled serves
an empty calendar, which clears the dates from every subscriber.
"""
import hashlib
from datetime import date, timedelta

from urllib.parse import quote

from flask import Blueprint, Response, jsonify, redirect, request

from app import limiter
from app.database.supabase_client import fetch_all, supabase
from app.knowledge.calendar import build_ics, calendar_key, dedupe_events, source_rank
from app.logging_config import error_logger

calendar_bp = Blueprint('calendar', __name__)

PAST_DAYS = 30  # keep last month's dates so a calendar doesn't look empty right after a collection


def _api_base() -> str:
    from app.public_url import public_api_base
    return public_api_base()


def _tenant(tenant_id):
    rows = (supabase.table('tenants').select("id, name, is_active, calendar_feeds, test_password_hash")
            .eq('id', str(tenant_id)).limit(1).execute()).data
    return rows[0] if rows else None


def _offered(tenant) -> bool:
    return bool(tenant) and tenant.get('is_active') is not False and bool(tenant.get('calendar_feeds')) \
        and not tenant.get('test_password_hash')


def _events(tenant_id):
    return fetch_all(lambda: (
        supabase.table('tenant_events')
        .select("series, zone, event_date, start_time, end_time, is_exception, notes, source_id, created_at")
        .eq('tenant_id', str(tenant_id))
        .gte('event_date', (date.today() - timedelta(days=PAST_DAYS)).isoformat())
        .order('event_date').order('id')
    ))


def feed_urls(tenant_id, key: str) -> dict:
    https = f"{_api_base()}/api/calendar/{tenant_id}/{key}.ics"
    webcal = "webcal://" + https.split("://", 1)[1]
    # the one link the chat shows: opens the visitor's own calendar app (see add_to_calendar)
    add = f"{_api_base()}/api/calendar/{tenant_id}/{key}/add"
    return {"https": https, "webcal": webcal, "add": add}


_APPLE = ("iphone", "ipad", "ipod", "macintosh", "mac os x")


def calendar_app_url(user_agent: str, webcal: str) -> str:
    """
    Where "In meinen Kalender" leads: Apple devices subscribe in their Calendar
    app (webcal://), everything else (Android, Windows, Linux) in Google
    Calendar, which syncs to the phone. Both stay up to date by themselves.
    """
    ua = (user_agent or "").lower()
    if any(a in ua for a in _APPLE) and "android" not in ua:
        return webcal
    return f"https://calendar.google.com/calendar/render?cid={quote(webcal, safe='')}"


@calendar_bp.route('/<uuid:tenant_id>/<string:keys>/add', methods=['GET'])
@limiter.limit("60 per minute")
def add_to_calendar(tenant_id, keys):
    """One link for every device: redirects to the calendar app that fits it."""
    webcal = feed_urls(tenant_id, keys)["webcal"]
    return redirect(calendar_app_url(request.headers.get('User-Agent', ''), webcal), code=302)


@calendar_bp.route('/<uuid:tenant_id>', methods=['GET'])
@limiter.limit("60 per minute")
def list_feeds(tenant_id):
    """The calendars a chatbot offers: one per series and zone with dates from today on."""
    try:
        tenant = _tenant(tenant_id)
        if not tenant:
            return jsonify({"error": "Not found"}), 404
        feeds = {}
        if _offered(tenant):
            today = date.today().isoformat()
            for e in dedupe_events(_events(tenant_id)):
                if e['event_date'] < today:
                    continue
                key = calendar_key(e['series'], e['zone'])
                feed = feeds.setdefault(key, {"key": key, "series": e['series'], "zone": e['zone'],
                                              "next": e['event_date'], "count": 0, **feed_urls(tenant_id, key)})
                feed["count"] += 1
        return jsonify({"enabled": _offered(tenant), "name": tenant['name'], "feeds": list(feeds.values())}), 200
    except Exception as e:
        error_logger.error(f"Error listing calendars for {tenant_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to list calendars"}), 500


@calendar_bp.route('/<uuid:tenant_id>/<string:keys>.ics', methods=['GET'])
@limiter.exempt
def get_feed(tenant_id, keys):
    """One or more series in one calendar: keys joined with '+'."""
    try:
        tenant = _tenant(tenant_id)
        if not tenant:
            return Response("Not found", status=404)
        wanted = {k for k in keys.split('+') if k}
        events = [e for e in _events(tenant_id) if calendar_key(e['series'], e['zone']) in wanted] if _offered(tenant) else []
        source_rows = {}
        source_ids = list({e['source_id'] for e in events if e.get('source_id')})
        for i in range(0, len(source_ids), 200):
            for s in supabase.table('tenant_sources').select("id, title, source_location") \
                    .in_('id', source_ids[i:i + 200]).execute().data or []:
                source_rows[s['id']] = s
        # an event read from several pages is one entry (and one UID), named after its own page
        events = dedupe_events(events, lambda e: source_rank(e, source_rows.get(e.get('source_id'))))

        labels = sorted({f"{e['series']} ({e['zone']})" if e['zone'] else e['series'] for e in events})
        title = f"{tenant['name']}: {', '.join(labels)}" if labels else tenant['name']
        sources = {sid: {"title": s.get('title') or '', "url": s.get('source_location') or ''}
                   for sid, s in source_rows.items()}
        # stamp from the data, not the clock, so an unchanged feed stays byte-identical (304s)
        from datetime import datetime, timezone
        newest = max((e.get('created_at') or '' for e in events), default='')
        stamp = datetime.fromisoformat(newest.replace('Z', '+00:00')) if newest else datetime(2026, 1, 1, tzinfo=timezone.utc)
        body = build_ics(
            tenant_id=str(tenant_id), title=title, events=events, sources=sources, now=stamp,
            description="Dates from the official documents, updated automatically. "
                        "To remove: delete or unsubscribe this calendar in your calendar app.",
        )

        etag = '"' + hashlib.sha1(body.encode()).hexdigest() + '"'
        if request.headers.get('If-None-Match') == etag:
            return Response(status=304, headers={"ETag": etag, "Cache-Control": "public, max-age=900"})
        return Response(body, mimetype='text/calendar', headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=900",
            "Content-Disposition": f'inline; filename="{keys[:60]}.ics"',
        })
    except Exception as e:
        error_logger.error(f"Error building calendar {keys} for {tenant_id}: {e}", exc_info=True)
        return Response("Calendar temporarily unavailable", status=503)
