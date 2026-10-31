"""
shared/knowledge/politeness.py

How fast the crawler may ask one website, shared by all scan workers through
Redis. Every request takes the next free slot of its site (crawl_tasks.py);
this module decides when a site gets a slower pace.

  429 / 503       the website said "too many requests": double the pause
                  for an hour, and hold everyone back for its Retry-After
  one timeout     usually a heavy page or our own browser limit: only that
                  page is retried, the site keeps its pace
  timeouts piling up   several within a minute: the site is probably
                  dropping our connections, so slow down after all
"""
import os
import time

HOST_INTERVAL_MS = int(os.getenv("CRAWL_HOST_INTERVAL_MS", "1000"))
MAX_HOST_INTERVAL_MS = 10_000
SLOW_PACE_SECONDS = 3600
# a worker waits at most this long for its slot (crawl_tasks._wait_for_host)
MAX_HOLD_MS = 120_000
TIMEOUTS_BEFORE_SLOWDOWN = 3
TIMEOUT_WINDOW_SECONDS = 60

PUSHBACK_STATUS = (429, 503)


def _interval_key(host: str) -> str:
    return f"crawl:interval:{host}"


def _next_key(host: str) -> str:
    return f"crawl:next:{host}"


def _timeouts_key(host: str) -> str:
    return f"crawl:timeouts:{host}"


def slow_down(r, host: str, retry_after: int | None = None) -> int:
    """Doubles the site's pause (for an hour); a Retry-After also holds its next slot back. Returns the new pause."""
    current = int(r.get(_interval_key(host)) or HOST_INTERVAL_MS)
    interval = min(MAX_HOST_INTERVAL_MS, current * 2)
    r.set(_interval_key(host), interval, ex=SLOW_PACE_SECONDS)
    if retry_after:
        hold_until = int(time.time() * 1000) + min(retry_after * 1000, MAX_HOLD_MS)
        if hold_until > int(r.get(_next_key(host)) or 0):
            r.set(_next_key(host), hold_until, px=max(MAX_HOLD_MS, 600_000))
    return interval


def note_timeout(r, host: str) -> bool:
    """Counts a page that didn't answer. True if that made the site slower (too many in a row)."""
    key = _timeouts_key(host)
    count = r.incr(key)
    if count == 1:
        r.expire(key, TIMEOUT_WINDOW_SECONDS)
    if count < TIMEOUTS_BEFORE_SLOWDOWN:
        return False
    r.delete(key)
    slow_down(r, host)
    return True


def after_failure(r, host: str, status_code: int, retry_after: int | None = None) -> bool:
    """A page couldn't be read: slow the site down if it pushed back. True if its pace changed."""
    if status_code in PUSHBACK_STATUS:
        slow_down(r, host, retry_after)
        return True
    return note_timeout(r, host)
