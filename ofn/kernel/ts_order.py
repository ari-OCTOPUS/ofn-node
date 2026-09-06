"""ts_order — per-run timestamps must not go backwards.

The store accepts any int ``ts``. ``seq`` proves order of *accepted*
appends. Neither proves a later record cannot carry an earlier clock.
This module is the kernel-pure second witness: within one run, each
accepted ``ts`` must be greater than or equal to the last accepted
``ts``. Equal is allowed (same-second appends). A smaller value fails
closed and leaves the cursor unchanged.

A missing last-ts is UNKNOWN (None), not 0 and not FALSE. Absence of
a prior event is not a proof of a second writer. Timeout is not an
input — elapsed budget is a different module.

Not wired into the run store (that file is owned by an open change).
Ordering a clock is not send_authorized, quote_sent, or
campaign_envelope_ready.

HALT stops STARTS. This index has no halt parameter: in-flight
ordering must still work so recovery does not need the owner.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Dict, Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A timestamp cursor never authorizes a send. Structurally False."""
    return False


def halt_blocks_ts_order() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight ordering."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. A backwards ts is a clock fact, not a writer."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. A missing last-ts is UNKNOWN, not FALSE."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready is not a rename of authorized."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")


def _require_run_id(run_id: object) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise FailClosedError(f"run_id required: {run_id!r}")
    _refuse_sealed(run_id, what="run_id")
    return run_id


def _require_ts(ts: object) -> int:
    if not isinstance(ts, int) or isinstance(ts, bool):
        raise FailClosedError(f"ts must be int: {ts!r}")
    return ts


class TsOrder:
    """Append-only per-run last-ts cursor. Replay does not write.

    Two independent claims:

      * first accept for a run records that ts
      * every later accept must be >= the recorded last ts
    """

    def __init__(self) -> None:
        self._last: Dict[str, int] = {}
        self._count: Dict[str, int] = {}

    def last(self, run_id: str) -> Optional[int]:
        """Last accepted ts, or None if this run has no prior event.

        None is UNKNOWN, not 0. Callers must not treat absence as a
        clock reading.
        """
        run_id = _require_run_id(run_id)
        return self._last.get(run_id)

    def accepted_count(self, run_id: str) -> int:
        run_id = _require_run_id(run_id)
        return self._count.get(run_id, 0)

    def accept(self, run_id: str, ts: int) -> int:
        run_id = _require_run_id(run_id)
        ts = _require_ts(ts)
        prior = self._last.get(run_id)
        if prior is not None and ts < prior:
            raise FailClosedError(
                f"ts went backwards on {run_id!r}: {ts} < {prior}")
        self._last[run_id] = ts
        self._count[run_id] = self._count.get(run_id, 0) + 1
        return ts

    def peek_would_accept(self, run_id: object, ts: object) -> bool:
        """True only when ``accept`` would succeed. Does not write.

        Invalid input is False, not an exception — peek is a read.
        """
        if not isinstance(run_id, str) or not run_id.strip():
            return False
        folded = run_id.strip().lower().replace("-", "_")
        if (is_forbidden_effect_name(run_id)
                or run_id.strip().lower() in _SEALED
                or folded in {s.replace("-", "_") for s in _SEALED}):
            return False
        if not isinstance(ts, int) or isinstance(ts, bool):
            return False
        prior = self._last.get(run_id)
        if prior is not None and ts < prior:
            return False
        return True


def compare_ts(prior: object, later: object) -> str:
    """Name the relation without mutating any cursor.

    Returns ``ok`` when later >= prior, ``backwards`` when later < prior.
    Missing / malformed values fail closed — UNKNOWN is not ordered.
    """
    a = _require_ts(prior)
    b = _require_ts(later)
    if b < a:
        return "backwards"
    return "ok"
