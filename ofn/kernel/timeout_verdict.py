"""timeout_verdict — a timeout is UNKNOWN, not a concurrent-write proof.

Evidence rules encoded structurally:

  * Timeout does not prove concurrent writing.
  * UNKNOWN is not FALSE.
  * Proposal is not execution.

The store and the worktree inventory already treat a hung writer as
an observation, not a second body. This module is the kernel-pure
vocabulary for that observation: elapsed and budget arrive as exact
ints; the kernel does not read a clock and does not inspect locks.

Equal elapsed == budget means the window is closed (TIMEOUT). A
completion witness wins over the clock — a late finish is still a
finish, not a timeout.

Not wired into the run store. Classifying a timeout is not
send_authorized, quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This classifier has no halt parameter: an
in-flight arm that overruns its budget must still be named so
recovery does not need the owner.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from .errors import FailClosedError
from .events import is_forbidden_effect_name

COMPLETED = "COMPLETED"
RUNNING = "RUNNING"
TIMEOUT = "TIMEOUT"

VERDICTS = frozenset({COMPLETED, RUNNING, TIMEOUT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A timeout verdict never authorizes a send. Structurally False."""
    return False


def halt_blocks_timeout() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight classification."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Elapsed budget is not a second writer."""
    return False


def timeout_is_false() -> bool:
    """Structurally False. TIMEOUT is UNKNOWN about the other side, not FALSE."""
    return False


def _require_nonneg_int(value: object, *, what: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise FailClosedError(f"{what} must be int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{what} must be non-negative: {value!r}")
    return value


def _require_bool(value: object, *, what: str) -> bool:
    if type(value) is not bool:
        raise FailClosedError(f"{what} must be bool: {value!r}")
    return value


def _refuse_sealed(value: object, *, what: str) -> None:
    if not isinstance(value, str):
        return
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or folded in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")


def classify_progress(
    *,
    elapsed_s: object,
    budget_s: object,
    completed: object,
) -> str:
    """Name one arm's progress from caller-supplied instants.

    completed=True  → COMPLETED (a finish witness beats the clock)
    elapsed >= budget and not completed → TIMEOUT (equal = closed)
    elapsed <  budget and not completed → RUNNING

    bool is not an int. A string clock is not a guess. 1 is not True.
    """
    _refuse_sealed(elapsed_s, what="elapsed_s")
    _refuse_sealed(budget_s, what="budget_s")
    elapsed = _require_nonneg_int(elapsed_s, what="elapsed_s")
    budget = _require_nonneg_int(budget_s, what="budget_s")
    done = _require_bool(completed, what="completed")
    if done:
        return COMPLETED
    if elapsed >= budget:
        return TIMEOUT
    return RUNNING


def concurrent_write_from_timeout(verdict: object) -> bool:
    """TIMEOUT never upgrades to a concurrent-write claim.

    Invalid input fails closed — UNKNOWN is not FALSE, and a
    malformed verdict is not a write proof either.
    """
    if not isinstance(verdict, str) or verdict not in VERDICTS:
        raise FailClosedError(f"unknown progress verdict: {verdict!r}")
    _refuse_sealed(verdict, what="verdict")
    return False
