"""Revenue-path states — ready is not authorized.

The last permitted stop on the owner-absent revenue path is
``campaign_envelope_ready``. ``send_authorized`` and ``quote_sent`` are
different names on purpose: no function in this module maps ready onto
either of them, and asking whether a ready state authorizes an external
effect always returns False (or fails closed if the caller passed a send
state, which this module does not grant).

Kernel purity: constants and a predicate. No I/O, no transport.
"""

from __future__ import annotations

from .errors import FailClosedError

CAMPAIGN_ENVELOPE_READY = "campaign_envelope_ready"
POLICY_CHECKED = "policy_checked"
QUOTE_DRAFTED = "quote_drafted"

SEND_AUTHORIZED = "send_authorized"
QUOTE_SENT = "quote_sent"

READY_STATES = frozenset({
    CAMPAIGN_ENVELOPE_READY,
    POLICY_CHECKED,
    QUOTE_DRAFTED,
})

SEND_STATES = frozenset({
    SEND_AUTHORIZED,
    QUOTE_SENT,
})


def authorizes_external_effect(state: str) -> bool:
    """Does this state authorize leaving the node?

    Ready states: False (structurally — not a missing flag).
    Send states: refused; this module does not grant them.
    Anything else: refused as unknown, not treated as authorized.
    """
    if not isinstance(state, str) or not state.strip():
        raise FailClosedError(f"state must be a non-empty name: {state!r}")
    if state in SEND_STATES:
        raise FailClosedError(
            f"{state!r} is not granted by this module — owner authorization "
            "is a later, scoped decision, not a rename of ready")
    if state in READY_STATES:
        return False
    raise FailClosedError(f"unknown revenue state: {state!r}")


def next_state_after_ready() -> None:
    """There is no next state here. A function that returned
    ``send_authorized`` would be the bug this file exists to prevent."""
    raise FailClosedError(
        "no transition from campaign_envelope_ready — send stays forbidden "
        "until an explicit, newer, scoped authorization exists")
