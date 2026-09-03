"""source_health — dead-source and rate-limit vocabulary (pure kernel).

The chaos rules this module encodes were already project law before it
existed; this just gives them one honest home:

  * a dead/errored source is UNKNOWN, never FALSE — absence of a witness
    is not a negative witness (paid for in PR #59: 403-as-policy);
  * 403 is PARKED immediately — forbidden is a policy answer, not traffic;
  * 429/5xx get BOUNDED backoff, then PARKED — no infinite retry;
    backoff delays are capped and enumerable, so "bounded" is checkable;
  * attempts / status / cap_s are exact ints — bool is not an int
    (the same scar CallBudget paid for: True < 3 is True);
  * once PARKED, a source stays PARKED — this module has no unpark.

A classification never grants send_authorized, quote_sent, or
campaign_envelope_ready. HALT is not a parameter: reading a source
is not a start.

Not wired into run_store or run_gate (those files are owned by open
changes). Callers import the predicates.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Dict, Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

OK = "OK"
UNKNOWN = "UNKNOWN"          # dead source / network error / no witness
RETRY_AFTER_BACKOFF = "RETRY_AFTER_BACKOFF"
PARKED = "PARKED"            # policy answer (403) or retries exhausted

VERDICTS = frozenset({OK, UNKNOWN, RETRY_AFTER_BACKOFF, PARKED})

_TRANSIENT = frozenset({429, 500, 502, 503, 504})
MAX_BACKOFF_ATTEMPTS = 3
BACKOFF_CAP_S = 60

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A fetch classification never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not source classification."""
    return False


def unpark_without_owner() -> bool:
    """Structurally False. This module records PARKED; it does not clear it."""
    return False


def _require_int(value: object, *, name: str,
                 min_value: Optional[int] = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    if min_value is not None and value < min_value:
        raise FailClosedError(f"{name} must be >= {min_value}: {value!r}")
    return value


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in _SEALED


def backoff_delays(attempts: int = MAX_BACKOFF_ATTEMPTS,
                   cap_s: int = BACKOFF_CAP_S) -> tuple:
    """Bounded exponential backoff schedule: 1, 2, 4s … capped. Enumerable
    on purpose — an unbounded retry loop cannot be shown to terminate.

    ``attempts`` and ``cap_s`` are exact non-negative ints. ``True`` is
    not 1. ``int()`` coercion is the bug this pin exists to prevent.
    """
    n = _require_int(attempts, name="attempts")
    cap = _require_int(cap_s, name="cap_s")
    return tuple(min(2 ** i, cap) for i in range(n))


def classify_fetch(status: Optional[int], *, attempts: int = 0,
                   error: Optional[BaseException] = None,
                   prior: Optional[str] = None) -> str:
    """Classify one fetch outcome.

    status=None means no response exists at all (dead source, timeout,
    DNS): UNKNOWN. A 403 is policy: PARKED, no retry, ever. 429/5xx are
    transient: RETRY_AFTER_BACKOFF while attempts remain, else PARKED.

    ``error`` is a first-class witness. A transport that also filled in
    a leftover status (e.g. 200 + TimeoutError) is UNKNOWN, not OK —
    a failure witness is not a successful fetch.

    ``prior=PARKED`` latches: a later 200 does not unpark. Other prior
    verdicts do not override this fetch. Unknown prior fails closed.

    ``status`` and ``attempts`` are exact ints (bool refused). A 401 or
    404 is UNKNOWN, not FALSE — missing or forbidden-to-us is not a
    negative witness.
    """
    if prior is not None:
        if prior == PARKED:
            return PARKED
        if prior not in VERDICTS:
            raise FailClosedError(f"unknown prior verdict: {prior!r}")
    if error is not None:
        return UNKNOWN
    if status is None:
        return UNKNOWN
    code = _require_int(status, name="status", min_value=None)
    tries = _require_int(attempts, name="attempts")
    if code == 403:
        return PARKED
    if code in _TRANSIENT:
        if tries < MAX_BACKOFF_ATTEMPTS:
            return RETRY_AFTER_BACKOFF
        return PARKED
    if 200 <= code < 300:
        return OK
    # 401 / 404 / everything else we cannot verify: UNKNOWN, not FALSE.
    return UNKNOWN


class ParkIndex:
    """Second witness of PARKED: once noted, a source stays parked.

    ``classify_fetch`` answers one attempt. This index answers history.
    Absence of a note is not OK — it is simply not yet parked.

    A recorded park is not a run and does not grant a send. There is
    no unpark method that succeeds.
    """

    def __init__(self) -> None:
        self._parked: Dict[str, str] = {}

    def note(self, source_id: str, verdict: str) -> str:
        if not isinstance(source_id, str) or not source_id.strip():
            raise FailClosedError(f"source_id required: {source_id!r}")
        if _is_sealed(source_id):
            raise FailClosedError(
                f"source_id cannot be a sealed effect name: {source_id!r}")
        if verdict not in VERDICTS:
            raise FailClosedError(f"unknown verdict: {verdict!r}")
        if source_id in self._parked:
            return PARKED
        if verdict == PARKED:
            self._parked[source_id] = PARKED
        return verdict

    def is_parked(self, source_id: str) -> bool:
        if not isinstance(source_id, str) or not source_id.strip():
            raise FailClosedError(f"source_id required: {source_id!r}")
        if _is_sealed(source_id):
            raise FailClosedError(
                f"source_id cannot be a sealed effect name: {source_id!r}")
        return source_id in self._parked

    def unpark(self, source_id: str) -> None:
        """Refused. Clearing PARKED is an owner decision, not a fetch."""
        raise FailClosedError(
            f"ParkIndex does not unpark {source_id!r} — owner decision")
