"""Bind a supplied name as CAMPAIGN_READY or UNKNOWN.

campaign_envelope_ready is a ready state, not send_authorized
and not quote_sent. Those two sealed send names fail closed
here — they are not a missing classification and they are
not a campaign bind.

Missing is UNKNOWN (None), not FALSE. Classification never
grants a send and never promotes ready to authorized.

Distinct from campaign_envelope.py (pack), ready_auth (other
open change), and kind_graph succession. Not wired into
run_store.py. HALT stops STARTS, not a bind.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

CAMPAIGN_READY = "CAMPAIGN_READY"
UNKNOWN = "UNKNOWN"

_READY = frozenset({
    "campaign_envelope_ready",
    "campaign-envelope-ready",
})
_SEND = frozenset({
    "send_authorized",
    "quote_sent",
    "send-authorized",
    "quote-sent",
})


def grants_send() -> bool:
    """A campaign bind never authorizes a send. Structurally False."""
    return False


def halt_blocks_bind() -> bool:
    """Structurally False. HALT stops STARTS, not this bind."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A bind is not a rename of authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A bind is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_send_name(value: str, *, what: str) -> None:
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded.replace("_", "-") in _SEND
        or folded in {s.replace("-", "_") for s in _SEND}
    ):
        if folded in {s.replace("-", "_") for s in _READY}:
            return
        raise FailClosedError(
            f"{what} names a sealed send state: {value!r} — "
            "ready is not authorized")


def classify_state(value: object) -> str:
    """CAMPAIGN_READY or UNKNOWN. Missing is UNKNOWN, not FALSE.

    send_authorized / quote_sent fail closed — they are not a
    campaign-ready class. An unknown present string fails closed
    (shape error), not UNKNOWN.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"state must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError("state is empty")
    _refuse_send_name(value, what="state")
    folded = _fold(value)
    if folded in {s.replace("-", "_") for s in _READY}:
        return CAMPAIGN_READY
    raise FailClosedError(f"unknown campaign state: {value!r}")


@dataclass(frozen=True)
class CampaignBind:
    """One campaign_envelope_ready name. Frozen so a later write
    cannot silently retcon it into send_authorized.
    """

    state: str
    state_class: str


def bind_ready(value: object) -> CampaignBind:
    """Require CAMPAIGN_READY. Missing fails closed (use try_bind)."""
    klass = classify_state(value)
    if klass == UNKNOWN:
        raise FailClosedError(
            "state missing — UNKNOWN is not a campaign bind")
    if type(value) is not str:
        raise FailClosedError(f"state must be a str: {value!r}")
    return CampaignBind(
        state="campaign_envelope_ready",
        state_class=CAMPAIGN_READY,
    )


def try_bind(value: object) -> Optional[CampaignBind]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    if value is None:
        return None
    return bind_ready(value)
