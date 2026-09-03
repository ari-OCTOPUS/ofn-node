"""Exact-int deadline window — second witness of the store's close rule.

The store refuses a create or append when ``now_epoch_s >= deadline``.
Equal means the window is closed. That check lives inline in an adapter
another open change already owns. This module is the kernel-pure copy:
both instants are caller-supplied ints; the kernel does not parse ISO
and does not read a clock.

Not wired into the run store. Accepting a window is not
send_authorized, quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This index has no halt parameter: in-flight
deadline checks must still work so recovery does not need the owner.

Kernel purity: typing + dataclasses + re. No json, no clock, no I/O,
no datetime (datetime is not on the kernel allowlist).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A deadline window never authorizes a send. Structurally False."""
    return False


def halt_blocks_deadline() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight windows."""
    return False


def _require_epoch(value: object, *, what: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise FailClosedError(f"{what} must be int: {value!r}")
    return value


def _require_run_id(run_id: object) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise FailClosedError(f"run_id required: {run_id!r}")
    if is_forbidden_effect_name(run_id) or run_id.strip().lower() in _SEALED:
        raise FailClosedError(
            f"run_id names a sealed send/ready state: {run_id!r}")
    if not RUN_ID_RE.match(run_id):
        raise FailClosedError(f"run_id not boundary-minted: {run_id!r}")
    return run_id


def window_open(now_epoch_s: int, deadline_epoch_s: int) -> bool:
    """True only when now is strictly before the deadline.

    Equal means the window is closed. Both values are exact ints —
    bool is not an int, and a missing clock is not a guess.
    """
    now = _require_epoch(now_epoch_s, what="now_epoch_s")
    deadline = _require_epoch(deadline_epoch_s, what="deadline_epoch_s")
    return now < deadline


def refuse_past_deadline(now_epoch_s: int, deadline_epoch_s: int) -> None:
    """Fail closed when the window is not open. Writes nothing."""
    if not window_open(now_epoch_s, deadline_epoch_s):
        raise FailClosedError(
            f"deadline passed: now={now_epoch_s!r} >= {deadline_epoch_s!r} "
            "— refusing (equal means the window is closed)")


class DeadlineIndex:
    """Append-only in-memory run → deadline map. Replay does not write.

    Two independent claims:

      * bind     — a run must have a persisted deadline before a check
      * refuse   — now >= bound deadline fails closed (equal = closed)
    """

    def __init__(self) -> None:
        self._bound: Dict[str, int] = {}
        self._order: List[str] = []

    def bind(self, run_id: str, deadline_epoch_s: int) -> bool:
        """Register a run's deadline. Same epoch re-bind is idempotent.

        A second bind to a *different* epoch fails closed — the
        deadline is part of the contract, not a moving target.
        Returns True on first bind, False on a no-op re-bind.
        """
        run_id = _require_run_id(run_id)
        deadline = _require_epoch(deadline_epoch_s, what="deadline_epoch_s")
        prior = self._bound.get(run_id)
        if prior is not None:
            if prior != deadline:
                raise FailClosedError(
                    f"run {run_id!r} already bound to deadline {prior!r}, "
                    f"refusing rebind to {deadline!r}")
            return False
        self._bound[run_id] = deadline
        self._order.append(run_id)
        return True

    def deadline_of(self, run_id: str) -> int:
        run_id = _require_run_id(run_id)
        if run_id not in self._bound:
            raise FailClosedError(
                f"run {run_id!r} has no persisted deadline — refusing")
        return self._bound[run_id]

    def is_open(self, run_id: str, now_epoch_s: int) -> bool:
        """True only when this run's window is still open at now."""
        return window_open(now_epoch_s, self.deadline_of(run_id))

    def refuse_if_closed(self, run_id: str, now_epoch_s: int) -> None:
        refuse_past_deadline(now_epoch_s, self.deadline_of(run_id))

    def known(self, run_id: str) -> bool:
        run_id = _require_run_id(run_id)
        return run_id in self._bound

    def __len__(self) -> int:
        return len(self._order)

    def replay(self) -> Tuple[Tuple[str, int], ...]:
        """Read-only snapshot in bind order. Has no write path."""
        return tuple((rid, self._bound[rid]) for rid in self._order)


def refuse_sealed_deadline_label(label: object) -> None:
    """A deadline is an epoch. A send/ready name is not a deadline label."""
    if not isinstance(label, str):
        raise FailClosedError(f"deadline label must be a string: {label!r}")
    if is_forbidden_effect_name(label) or label.strip().lower() in _SEALED:
        raise FailClosedError(
            f"deadline label names a sealed send/ready state: {label!r}")
