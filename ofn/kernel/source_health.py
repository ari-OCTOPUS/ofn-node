"""source_health — dead-source and rate-limit vocabulary (pure kernel).

The chaos rules this module encodes were already project law before it
existed; this just gives them one honest home:

  * a dead/errored source is UNKNOWN, never FALSE — absence of a witness
    is not a negative witness (paid for in PR #59: 403-as-policy);
  * 403 is PARKED immediately — forbidden is a policy answer, not traffic;
  * 429/5xx get BOUNDED backoff, then PARKED — no infinite retry;
  * backoff delays are capped and enumerable, so "bounded" is checkable.

Kernel purity: no imports beyond typing; everything arrives as arguments.
"""

from __future__ import annotations

from typing import Optional

OK = "OK"
UNKNOWN = "UNKNOWN"          # dead source / network error / no witness
RETRY_AFTER_BACKOFF = "RETRY_AFTER_BACKOFF"
PARKED = "PARKED"            # policy answer (403) or retries exhausted

_TRANSIENT = frozenset({429, 500, 502, 503, 504})
MAX_BACKOFF_ATTEMPTS = 3
BACKOFF_CAP_S = 60


def backoff_delays(attempts: int = MAX_BACKOFF_ATTEMPTS,
                   cap_s: int = BACKOFF_CAP_S) -> tuple:
    """Bounded exponential backoff schedule: 1, 2, 4s … capped. Enumerable
    on purpose — an unbounded retry loop cannot be shown to terminate."""
    n = max(0, int(attempts))
    return tuple(min(2 ** i, cap_s) for i in range(n))


def classify_fetch(status: Optional[int], *, attempts: int = 0,
                   error: Optional[BaseException] = None) -> str:
    """Classify one fetch outcome.

    status=None means no response exists at all (dead source, timeout,
    DNS): UNKNOWN. A 403 is policy: PARKED, no retry, ever. 429/5xx are
    transient: RETRY_AFTER_BACKOFF while attempts remain, else PARKED.
    """
    if status is None:
        return UNKNOWN
    if status == 403:
        return PARKED
    if status in _TRANSIENT:
        if attempts < MAX_BACKOFF_ATTEMPTS:
            return RETRY_AFTER_BACKOFF
        return PARKED
    if 200 <= status < 300:
        return OK
    return UNKNOWN
