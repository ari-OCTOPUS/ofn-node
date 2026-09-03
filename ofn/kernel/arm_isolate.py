"""arm_isolate — one arm's timeout parks that arm; others continue.

Owner-absence Scenario 2: an agent timeout must not stop the other
arms. This module is the kernel-pure latch for that rule.

Complementary to, and not a replacement for:

  * ``kernel.source_health`` — fetch/backoff/PARK for a *source*
    (owned by an open change)
  * ``kernel.timeout_verdict`` — name one overrun (this lane)
  * ``kernel.start_permit`` — HALT refuses STARTS (owned by an open change)

A timeout parks the named arm. An unseen arm is UNKNOWN, not FALSE
and not PARKED — absence of a timeout witness is not a death
certificate. UNKNOWN and RUNNING both remain continue-eligible.
Once PARKED, the latch holds; ``unpark`` is refused without an
owner grant this module cannot invent.

Timeout does not prove concurrent writing. HALT is not a parameter
(stops STARTS, not in-flight isolation). Not wired into the run
store. Parking an arm is not send_authorized, quote_sent, or
campaign_envelope_ready.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .timeout_verdict import (
    TIMEOUT,
    classify_progress,
    timeout_proves_concurrent_write,
)

UNKNOWN = "UNKNOWN"
RUNNING = "RUNNING"
PARKED = "PARKED"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """Parking an arm never authorizes a send. Structurally False."""
    return False


def halt_blocks_isolate() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight isolation."""
    return False


def unpark_without_owner() -> bool:
    """Structurally False. This module cannot invent an unpark grant."""
    return False


def _require_arm(arm: object) -> str:
    if not isinstance(arm, str) or not arm.strip():
        raise FailClosedError(f"arm name required: {arm!r}")
    folded = arm.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(arm) or folded in _SEALED:
        raise FailClosedError(
            f"arm names a sealed send/ready state: {arm!r}")
    return arm.strip()


class ArmIndex:
    """Append-only in-memory arm → status latch. Replay does not write.

    Two independent claims:

      * note_timeout  — that arm becomes PARKED and stays PARKED
      * others        — every other roster member stays continue-eligible
                        unless it was itself parked
    """

    def __init__(self) -> None:
        self._status: Dict[str, str] = {}
        self._order: List[str] = []

    def status(self, arm: object) -> str:
        name = _require_arm(arm)
        return self._status.get(name, UNKNOWN)

    def continue_eligible(self, arm: object) -> bool:
        """True unless this arm is PARKED.

        UNKNOWN (never noted) is eligible — no timeout witness is
        not a park. RUNNING is eligible. PARKED is not.
        """
        return self.status(arm) != PARKED

    def note_progress(self, arm: object) -> str:
        """Mark an arm RUNNING unless it is already PARKED (latch)."""
        name = _require_arm(arm)
        current = self._status.get(name)
        if current == PARKED:
            return PARKED
        if current is None:
            self._order.append(name)
        self._status[name] = RUNNING
        return RUNNING

    def note_timeout(self, arm: object) -> str:
        """Park one arm. Does not touch any other arm.

        Calling this is not proof another writer exists.
        """
        name = _require_arm(arm)
        if name not in self._status:
            self._order.append(name)
        self._status[name] = PARKED
        return PARKED

    def note_classified(
        self,
        arm: object,
        *,
        elapsed_s: object,
        budget_s: object,
        completed: object,
    ) -> str:
        """Apply ``classify_progress`` to one arm. TIMEOUT parks it.

        COMPLETED and RUNNING note progress. The classifier is the
        first witness; this latch is the second.
        """
        verdict = classify_progress(
            elapsed_s=elapsed_s, budget_s=budget_s, completed=completed)
        if verdict == TIMEOUT:
            return self.note_timeout(arm)
        self.note_progress(arm)
        return verdict

    def others_continue(
        self, parked_arm: object, roster: Sequence[object],
    ) -> Tuple[str, ...]:
        """Read-only: roster members that may keep working.

        ``parked_arm`` is excluded even if the caller has not noted
        the timeout yet — the argument is the isolation claim, not a
        write. Members already PARKED stay out. UNKNOWN members stay
        in (no witness ≠ park).
        """
        isolated = _require_arm(parked_arm)
        if not isinstance(roster, (list, tuple)):
            raise FailClosedError(f"roster must be a sequence: {roster!r}")
        kept: List[str] = []
        for item in roster:
            name = _require_arm(item)
            if name == isolated:
                continue
            if self.continue_eligible(name):
                kept.append(name)
        return tuple(kept)

    def unpark(self, arm: object) -> None:
        """Refused. Clearing a park is an owner grant this module lacks."""
        name = _require_arm(arm)
        raise FailClosedError(
            f"unpark of {name!r} refused — no owner grant on this module")

    def peek_status(self, arm: object) -> str:
        """Read-only alias of ``status``. Has no write path."""
        return self.status(arm)

    def replay(self) -> Tuple[Tuple[str, str], ...]:
        """Read-only snapshot in note order. Has no write path."""
        return tuple((name, self._status[name]) for name in self._order)

    def __len__(self) -> int:
        return len(self._order)


# Re-export so a caller that only imported this module can still
# name the evidence pin without reaching into timeout_verdict.
timeout_is_not_a_second_writer = timeout_proves_concurrent_write
