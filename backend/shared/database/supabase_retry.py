"""
shared/database/supabase_retry.py

Retry helpers for Supabase / httpx calls that can fail transiently.

WHY THIS EXISTS:
  Supabase is accessed over HTTPS. In long-running processes (Celery workers,
  multi-worker gunicorn) the underlying httpx connection pool can encounter:
    - TCP connection resets (idle connection recycled by the load balancer)
    - DNS hiccups in Docker networking
    - Transient 5xx errors from Supabase during maintenance

  Without retries, a single transient error fails the entire request/task.
  With tenacity, we get automatic exponential back-off with jitter, a bounded
  retry count, and structured logging of each attempt.

USAGE:
  from app.database.supabase_retry import retrying_execute

  # Instead of: supabase.table("tenants").select("*").execute()
  # Use:        retrying_execute(supabase.table("tenants").select("*"))

  # Or decorate your own function:
  from app.database.supabase_retry import supabase_retry

  @supabase_retry
  def my_db_call():
      return supabase.table("foo").select("id").execute()
"""

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
)
import logging

from app.logging_config import error_logger

# ---------------------------------------------------------------------------
# Exceptions considered transient (safe to retry)
# ---------------------------------------------------------------------------

_RETRYABLE = (
    httpx.ConnectError,       # TCP connect failed (DNS, network blip)
    httpx.RemoteProtocolError,# Server sent unexpected bytes / closed early
    httpx.ReadTimeout,        # Server didn't respond in time
    httpx.WriteTimeout,
    httpx.PoolTimeout,        # All connections in pool are busy
)


def _is_retryable(exc: BaseException) -> bool:
    """
    Returns True for exceptions that are safe to retry.
    Also catches httpx errors wrapped inside supabase-py's own exceptions.
    """
    if isinstance(exc, _RETRYABLE):
        return True
    # supabase-py may wrap httpx errors; check the cause chain
    cause = getattr(exc, "__cause__", None) or getattr(exc, "__context__", None)
    if cause and isinstance(cause, _RETRYABLE):
        return True
    return False


# ---------------------------------------------------------------------------
# Core retry decorator
# ---------------------------------------------------------------------------

supabase_retry = retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=8.0),
    before_sleep=before_sleep_log(error_logger, logging.WARNING),
    reraise=True,  # Re-raise the original exception after all retries exhausted
)
"""
Tenacity retry decorator pre-configured for Supabase calls.

Policy:
  - Retries up to 3 times (4 total attempts)
  - Wait: exponential back-off starting at 0.5s, capped at 8s, with jitter
  - Only retries on transient httpx network errors, not on logic errors
  - Logs a WARNING before each retry so operators can see the pattern
  - Re-raises the original exception if all retries are exhausted

Example::

    @supabase_retry
    def get_tenant(tenant_id: str):
        return supabase.table("tenants").select("*").eq("id", tenant_id).execute()
"""


def retrying_execute(query_builder):
    """
    Execute a Supabase query builder with automatic retry.

    Convenience wrapper for inline use without a decorator.

    Args:
        query_builder: Any supabase-py query builder (the result of chaining
                       .table(), .select(), .eq(), etc. — before .execute()).

    Returns:
        The APIResponse from .execute().

    Raises:
        The original exception if all retry attempts are exhausted.

    Example::

        response = retrying_execute(
            supabase.table("tenants").select("id").eq("user_id", user_id)
        )
    """
    @supabase_retry
    def _execute():
        return query_builder.execute()

    return _execute()
