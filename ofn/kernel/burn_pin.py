"""Pin: an idempotency key is never burned by this module.

A refused write, a ready state, a missing key, or a cited
receipt does not consume the key. Burning belongs to the
store that already owns create-level collapse — this pin
is the independent record that a burn request was refused.

Missing is UNKNOWN (None), not FALSE. Timeout does not
prove a writer. A later disarm/hold still supersedes an
older authorization claim.

quote_sent and send_authorized are sealed and refused as
keys and as outcomes. PROPOSAL is not execution.

Distinct from idempotency.py, receipts.py, dedup.py,
write_fence.py, and key_class.py. Not wired into
run_store.py. HALT stops STARTS, not this pin.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .key_class import (
    KEY_BOUND,
    UNKNOWN,
    classify_key,
    is_sealed_key,
)

CAMPAIGN_ENVELOPE_READY = "campaign_envelope_ready"
SEND_AUTHORIZED = "send_authorized"
QUOTE_SENT = "quote_sent"

# Closed vocabularies. Widen only with a test.
OUTCOMES = frozenset({"refused", "ready", "missing", "receipt_cited"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "missing_key",
    "ready_does_not_burn",
    "refuse_does_not_burn",
    "pin_does_not_burn",
    "unknown_outcome",
})


def grants_send() -> bool:
    """A burn pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A pin is not an external effect."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def burns_on_refuse() -> bool:
    """Structurally False. A refused write does not consume the key."""
    return False


def burns_on_ready() -> bool:
    """Structurally False. Ready is not a burn and not a send."""
    return False


def burns_on_missing() -> bool:
    """Structurally False. Missing is UNKNOWN, not a consumed key."""
    return False


def burns_on_receipt() -> bool:
    """Structurally False. Citing a receipt does not burn here."""
    return False


def _require_outcome(value: object) -> str:
    if type(value) is not str or not value.strip():
        raise FailClosedError(f"outcome must be a non-empty str: {value!r}")
    name = value.strip()
    if is_sealed_key(name) or is_forbidden_effect_name(name):
        raise FailClosedError(
            f"outcome names a sealed send/ready state: {value!r}")
    if name not in OUTCOMES:
        raise FailClosedError(
            f"unknown outcome is not a refusal and not a grant: {name!r}")
    return name


def _reason_for(outcome: str) -> str:
    if outcome == "refused":
        return "refuse_does_not_burn"
    if outcome == "ready":
        return "ready_does_not_burn"
    if outcome == "missing":
        return "missing_key"
    if outcome == "receipt_cited":
        return "pin_does_not_burn"
    raise FailClosedError(f"unknown outcome: {outcome!r}")


@dataclass(frozen=True)
class BurnDecision:
    """The burn-admission verdict. ``burned`` and ``grants_send``
    are structurally False. Two independent claims live on the
    same object so a silent default cannot masquerade as a burn
    or a send.
    """

    burned: bool
    allowed: bool
    reason: str
    key_class: str
    outcome: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "BurnDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a burn pin is not a send")
        if self.burned:
            raise FailClosedError(
                "BurnDecision cannot burn an idempotency key")
        if self.allowed:
            raise FailClosedError(
                "BurnDecision cannot allow a burn")
        if self.reason not in REFUSAL_REASONS:
            raise FailClosedError(
                f"unknown or missing refusal reason: {self.reason!r}")
        if self.key_class not in {KEY_BOUND, UNKNOWN}:
            raise FailClosedError(
                f"unknown key_class is not a refusal and not a grant: "
                f"{self.key_class!r}")
        if self.outcome not in OUTCOMES and self.outcome != UNKNOWN:
            raise FailClosedError(
                f"unknown or missing outcome: {self.outcome!r}")
        if self.reason == "sealed_effect":
            return
        if self.key_class == UNKNOWN and self.reason not in {
            "missing_key", "unknown_outcome",
        }:
            raise FailClosedError(
                "UNKNOWN key_class must record missing_key or unknown_outcome")


def admit_burn(*, key: object, outcome: object) -> Optional[BurnDecision]:
    """May this pin burn this key after this outcome?

    True is unreachable. Missing key or missing outcome is None
    (UNKNOWN), not False and not a burn. Sealed send/ready names
    fail closed — presenting them as a key or an outcome is a
    shape error, not a yes.

    ``receipt_cited`` still refuses: this pin does not consume
    the key. The store that collapses create-level duplicates
    is a different module.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``, no ``now``. Tests lock the parameter list; the
    kernel does not import inspect.
    """
    if key is None or outcome is None:
        return None

    if is_sealed_key(key) or is_sealed_key(outcome):
        raise FailClosedError(
            f"refusing admit_burn key={key!r} outcome={outcome!r} — "
            "a sealed send/ready name is not a key and not an outcome")

    klass = classify_key(key)
    named = _require_outcome(outcome)
    if klass == UNKNOWN:
        raise FailClosedError("key missing after present check")

    return BurnDecision(
        burned=False,
        allowed=False,
        reason=_reason_for(named),
        key_class=klass,
        outcome=named,
    )
