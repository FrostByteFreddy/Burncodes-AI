"""
Abuse protection for the public chat endpoints.

The chat page and widget are anonymous, so every limit here is keyed by
something an attacker cannot mint for free: the client IP (behind our one
trusted proxy hop) or the chatbot being asked. Status polling holds a server
thread for up to 30 s, so it only answers for task ids we issued and only a
few at a time per IP.
"""
import os
from contextlib import contextmanager

import redis

# Limits use flask-limiter syntax; tune per deployment without a code change.
# Per-IP limits stay generous: an office or a mobile carrier puts many real
# people behind one address.
CHAT_LIMIT_PER_IP = os.environ.get("CHAT_LIMIT_PER_IP", "10 per minute;200 per hour")
# Caps what a botnet rotating IPs can cost one customer
CHAT_LIMIT_PER_TENANT = os.environ.get("CHAT_LIMIT_PER_TENANT", "600 per hour")
STATUS_LIMIT_PER_IP = os.environ.get("CHAT_STATUS_LIMIT_PER_IP", "120 per minute")
MAX_LONG_POLLS_PER_IP = int(os.environ.get("CHAT_MAX_LONG_POLLS_PER_IP", "10"))

TASK_TTL_SECONDS = 15 * 60

_redis = None


def _client():
    # created on first use so importing the app needs no Redis (tests swap in a fake)
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"))
    return _redis


def remember_task(task_id: str) -> None:
    _client().set(f"chat:task:{task_id}", 1, ex=TASK_TTL_SECONDS)


def is_known_task(task_id: str) -> bool:
    return bool(_client().exists(f"chat:task:{task_id}"))


@contextmanager
def long_poll_slot(ip: str):
    """Yields True if this IP may hold a waiting connection, False to answer at once."""
    r = _client()
    key = f"chat:polls:{ip}"
    count = r.incr(key)
    # safety net if a worker dies between incr and decr
    r.expire(key, 60)
    try:
        yield count <= MAX_LONG_POLLS_PER_IP
    finally:
        r.decr(key)
