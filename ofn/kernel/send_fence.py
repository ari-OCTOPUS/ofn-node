"""Fence: campaign_envelope_ready cannot become send_authorized.

A later disarm/hold supersedes an older authorization claim.
This fence never grants a send. Missing is UNKNOWN (None),
not FALSE. Timeout does not prove a writer.

quote_sent is a sealed external effect and is refused as a
promotion target. PROPOSAL is not execution.

Distinct from later_hold / scoped_authz (other open change),
campaign_envelope.py, and receipt_bind. Not wired into
run_store.py. HALT stops STARTS, not this fence.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Optional

from .campaign_bind import CAMPAIGN_READY, UNKNOWN, classify_state
from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

SEND_AUTHORIZED = "send_authorized"
QUOTE_SENT = "quote_sent"
CAMPAIGN_ENVELOPE_READY = "campaign_envelope_ready"

_SEND = frozenset({
    SEND_AUTHORIZED,
    QUOTE_SENT,
    "send-authorized",
    "quote-sent",
})
_READY = frozenset({
    CAMPAIGN_ENVELOPE_READY,
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A send fence never authorizes a send. Structurally False."""
    return False


def halt_blocks_fence() -> bool:
    """Structurally False. HALT stops STARTS, not this fence."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A fence is not an external effect."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def claims_immutable() -> bool:
    """Structurally False. A fence is not filesystem immutability."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _named(value: object, *, what: str) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"{what} must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError(f"{what} is empty")
    folded = _fold(value)
    if folded in {s.replace("-", "_") for s in _READY}:
        return CAMPAIGN_ENVELOPE_READY
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {s.replace("-", "_") for s in _SEND}
    ):
        if folded == "send_authorized":
            return SEND_AUTHORIZED
        if folded == "quote_sent":
            return QUOTE_SENT
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")
    raise FailClosedError(f"unknown fence name: {value!r}")


def admit_send(state: object) -> Optional[bool]:
    """True is unreachable. Ready is False. Missing is None.

    send_authorized / quote_sent fail closed — presenting them as
    an admit request is a shape error, not a yes.
    """
    named = _named(state, what="state")
    if named is None:
        return None
    if named == CAMPAIGN_ENVELOPE_READY:
        return False
    raise FailClosedError(
        f"refusing admit_send({named!r}) — later disarm supersedes "
        "and this fence never grants a send")


def promote(from_state: object, to_state: object) -> Optional[str]:
    """Refuse every promotion that would invent a send.

    Same-state re-state returns the canonical name. Missing either
    side is UNKNOWN (None), not False. Ready cannot become
    authorized. Authorized cannot become quote_sent.
    """
    src = _named(from_state, what="from_state")
    dst = _named(to_state, what="to_state")
    if src is None or dst is None:
        return None
    if src == dst:
        if src == CAMPAIGN_ENVELOPE_READY:
            klass = classify_state(src)
            if klass not in (CAMPAIGN_READY, UNKNOWN):
                raise FailClosedError("ready class drifted")
        return src
    raise FailClosedError(
        f"refusing promotion {src} → {dst} — ready is not authorized")
