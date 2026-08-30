"""
Shared external-I/O resilience (P8): exponential backoff + jitter, Retry-After
respect, and idempotency keys for Serper / Anthropic calls.

Design constraints (Brushline governance):
  - check_and_enforce runs BEFORE every attempt via `before_attempt` -- backoff
    can never bypass the per-day spend cap or the kill switch. A cap/kill-switch
    exception is NOT retryable: it propagates immediately.
  - Only transient failures are retried (429, 5xx, network / timeout). Anything
    else propagates on the first failure.
  - Each retry is audit-logged (IO_RETRY) so backoff is observable.
  - Cost is logged by the caller AFTER success, so retries never double-charge;
    a stable idempotency key lets the upstream API dedupe a retried request.
"""
from __future__ import annotations

import logging
import random
import time
import uuid

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def new_idempotency_key() -> str:
    """Stable key for one logical operation; reused across its retries."""
    return str(uuid.uuid4())


def _status_of(exc):
    resp = getattr(exc, "response", None)
    if resp is not None and getattr(resp, "status_code", None) is not None:
        return resp.status_code
    return getattr(exc, "status_code", None)


def is_retryable(exc) -> bool:
    if _status_of(exc) in _RETRYABLE_STATUS:
        return True
    name = type(exc).__name__.lower()
    return any(k in name for k in ("timeout", "connect", "network", "requesterror"))


def _retry_after(exc):
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None) or getattr(exc, "headers", None)
    if headers:
        try:
            val = headers.get("retry-after", headers.get("Retry-After"))
            if val is not None:
                return float(val)
        except Exception:
            return None
    return None


def call_with_retry(op, *, agent_id="io", before_attempt=None,
                    max_attempts=3, base_delay=0.5, max_delay=8.0,
                    retryable=is_retryable, sleep=time.sleep, audit_log=True):
    """
    Run op() with retry on transient failures.

    op:             zero-arg callable performing ONE external attempt.
    before_attempt: optional zero-arg callable run before EACH attempt (put
                    check_and_enforce here). Its exceptions are NOT retried.
    Returns op()'s result, or re-raises the last exception after max_attempts.
    """
    last = None
    for attempt in range(1, int(max_attempts) + 1):
        if before_attempt is not None:
            before_attempt()  # governance gate -- exceptions propagate (never retried)
        try:
            return op()
        except Exception as exc:
            last = exc
            if attempt >= max_attempts or not retryable(exc):
                raise
            delay = _retry_after(exc)
            if delay is None:
                delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                delay += random.uniform(0, base_delay)  # full jitter component
            if audit_log:
                try:
                    from . import audit
                    audit.append("IO_RETRY", agent_id, {
                        "attempt": attempt,
                        "max_attempts": int(max_attempts),
                        "delay_sec": round(delay, 3),
                        "error": type(exc).__name__,
                        "status": _status_of(exc),
                    })
                except Exception:
                    pass
            sleep(delay)
    raise last
