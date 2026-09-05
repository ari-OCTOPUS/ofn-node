"""Classify a later hold against an older authorization epoch.

A later hold (hold_epoch > authz_epoch) supersedes that claim.
An older hold does not supersede, and still does not grant a send.
Missing either epoch is UNKNOWN (None), not FALSE and not 0.

Same-epoch is a shape error, not later. Bool/float/str epochs
fail closed. Sealed send/ready names are not epochs.

This module never grants a send and never re-arms after a hold.
campaign_envelope_ready stays distinct from send_authorized.

Distinct from send_fence (name promotion), campaign_bind (ready
class), phase_wall / flag_freeze (bool later_hold parameter),
and hold_class / disarm_pin (other open change). Not wired into
run_store.py. HALT stops STARTS, not this classify.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name, require_epoch_s
from .errors import FailClosedError
from .events import is_forbidden_effect_name

LATER_HOLD = "LATER_HOLD"
OLDER_HOLD = "OLDER_HOLD"
UNKNOWN = "UNKNOWN"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A later-hold classify never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A later hold does not re-arm outbound."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A hold class is not a rename of authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A hold class is not an external effect."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This module is not imported by the store."""
    return False


def later_supersedes_older() -> bool:
    """Structurally True. A later hold beats an older authorization."""
    return True


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed_name(value: object, *, what: str) -> None:
    if type(value) is not str:
        return
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {s.replace("-", "_") for s in _SEALED}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "a hold epoch is not a send")


def _epoch_or_unknown(value: object, *, what: str) -> Optional[int]:
    if value is None:
        return None
    _refuse_sealed_name(value, what=what)
    return require_epoch_s(value, what)


def classify_hold(hold_epoch: object, authz_epoch: object) -> str:
    """LATER_HOLD, OLDER_HOLD, or UNKNOWN.

    Missing either side is UNKNOWN, not FALSE. Equal epochs fail
    closed — same instant is not later. Present-but-bad still
    fails closed (shape error), not UNKNOWN.
    """
    hold = _epoch_or_unknown(hold_epoch, what="hold_epoch")
    authz = _epoch_or_unknown(authz_epoch, what="authz_epoch")
    if hold is None or authz is None:
        return UNKNOWN
    if hold == authz:
        raise FailClosedError(
            "hold_epoch equals authz_epoch — same epoch is not later")
    if hold > authz:
        return LATER_HOLD
    return OLDER_HOLD


def supersedes(hold_epoch: object, authz_epoch: object) -> Optional[bool]:
    """True only when hold is later. Missing is None, not False.

    Older hold returns False (does not supersede). Equal / bad
    shapes fail closed. False is not a send grant.
    """
    klass = classify_hold(hold_epoch, authz_epoch)
    if klass == UNKNOWN:
        return None
    if klass == LATER_HOLD:
        return True
    return False


def admit_send_after_hold(
    hold_epoch: object, authz_epoch: object,
) -> Optional[bool]:
    """True is unreachable. Later or older is False. Missing is None.

    Present-but-bad still fails closed. Ready/send names as epochs
    fail closed — they are not a missing classification.
    """
    klass = classify_hold(hold_epoch, authz_epoch)
    if klass == UNKNOWN:
        return None
    return False


@dataclass(frozen=True)
class LaterHold:
    """One hold-vs-authz class. Frozen so a later write cannot
    silently retcon LATER_HOLD into a send grant.
    """

    hold_epoch: int
    authz_epoch: int
    hold_class: str


def pin_later(hold_epoch: object, authz_epoch: object) -> LaterHold:
    """Require LATER_HOLD. Missing fails closed (use try_pin)."""
    klass = classify_hold(hold_epoch, authz_epoch)
    if klass == UNKNOWN:
        raise FailClosedError(
            "epoch missing — UNKNOWN is not a later-hold pin")
    if klass != LATER_HOLD:
        raise FailClosedError(
            f"hold is {klass}, not LATER_HOLD — older does not pin later")
    hold = require_epoch_s(hold_epoch, "hold_epoch")
    authz = require_epoch_s(authz_epoch, "authz_epoch")
    return LaterHold(
        hold_epoch=hold,
        authz_epoch=authz,
        hold_class=LATER_HOLD,
    )


def try_pin(hold_epoch: object, authz_epoch: object) -> Optional[LaterHold]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    if hold_epoch is None or authz_epoch is None:
        return None
    return pin_later(hold_epoch, authz_epoch)
