"""
The crawler's pace per website: only real pushback slows a site down, one
slow page doesn't (younity was held at 10 s per page by our own timeouts).
"""
import time

from app.knowledge import politeness as p


class FakeRedis:
    """The few Redis calls politeness uses, in memory (expiry is only recorded)."""

    def __init__(self):
        self.data, self.ttl = {}, {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None, px=None):
        self.data[key] = str(value)
        self.ttl[key] = ex if ex is not None else (px / 1000 if px else None)

    def incr(self, key):
        self.data[key] = str(int(self.data.get(key) or 0) + 1)
        return int(self.data[key])

    def expire(self, key, seconds):
        self.ttl[key] = seconds

    def delete(self, key):
        self.data.pop(key, None)


def _pace(r, host="site.ch"):
    return int(r.get(f"crawl:interval:{host}") or p.HOST_INTERVAL_MS)


def test_too_many_requests_slows_the_site_down():
    r = FakeRedis()
    assert p.after_failure(r, "site.ch", 429) is True
    assert _pace(r) == p.HOST_INTERVAL_MS * 2
    assert r.ttl["crawl:interval:site.ch"] == p.SLOW_PACE_SECONDS
    p.after_failure(r, "site.ch", 503)
    assert _pace(r) == p.HOST_INTERVAL_MS * 4


def test_the_pace_never_drops_below_one_page_per_ten_seconds():
    r = FakeRedis()
    for _ in range(10):
        p.after_failure(r, "site.ch", 429)
    assert _pace(r) == p.MAX_HOST_INTERVAL_MS


def test_retry_after_holds_every_worker_back():
    r = FakeRedis()
    before = int(time.time() * 1000)
    p.after_failure(r, "site.ch", 429, retry_after=30)
    assert int(r.get("crawl:next:site.ch")) >= before + 30_000
    # never longer than a worker waits for its slot
    p.after_failure(r, "site.ch", 429, retry_after=3600)
    assert int(r.get("crawl:next:site.ch")) <= int(time.time() * 1000) + p.MAX_HOLD_MS


def test_one_timeout_only_retries_that_page():
    r = FakeRedis()
    assert p.after_failure(r, "site.ch", 408) is False
    assert p.after_failure(r, "site.ch", 0) is False   # no connection
    assert _pace(r) == p.HOST_INTERVAL_MS


def test_timeouts_piling_up_slow_the_site_down():
    r = FakeRedis()
    results = [p.after_failure(r, "site.ch", 408) for _ in range(p.TIMEOUTS_BEFORE_SLOWDOWN)]
    assert results == [False] * (p.TIMEOUTS_BEFORE_SLOWDOWN - 1) + [True]
    assert _pace(r) == p.HOST_INTERVAL_MS * 2
    # the count starts over, and only within the window
    assert r.get("crawl:timeouts:site.ch") is None
    p.after_failure(r, "site.ch", 408)
    assert r.ttl["crawl:timeouts:site.ch"] == p.TIMEOUT_WINDOW_SECONDS


def test_sites_are_paced_separately():
    r = FakeRedis()
    p.after_failure(r, "slow.ch", 429)
    assert _pace(r, "fast.ch") == p.HOST_INTERVAL_MS
