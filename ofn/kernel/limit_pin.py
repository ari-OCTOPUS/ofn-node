"""Pin a ScopeBind so the action cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (run_id → action). The same pair
again is already_limited. A different action on the same run_id
fails closed as action_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .scope_class import (
    START,
    ScopeBind,
    bind_scope,
    classify_action,
)

LIMITED = "limited"
ALREADY_LIMITED = "already_limited"

_SEALED_ACTIONS = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A limit pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A pin is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def consumes_nonce() -> bool:
    """Structurally False. This pin is not nonce once-consume."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def pin_allows_send(bind: ScopeBind) -> bool:
    """Structurally False. Even a start bind is not send_authorized."""
    if not isinstance(bind, ScopeBind):
        raise FailClosedError(f"bind must be a ScopeBind: {bind!r}")
    return False


def pin_allows_start(bind: ScopeBind) -> bool:
    """True only when the pinned action is start.

    This is not a grant of starting and not send_authorized.
    HALT still stops the factory START.
    """
    if not isinstance(bind, ScopeBind):
        raise FailClosedError(f"bind must be a ScopeBind: {bind!r}")
    return bind.action == START


def peek_limit(table: Mapping[str, str], run_id: object) -> Optional[str]:
    """Return the pinned action or None.

    None is UNKNOWN, not FALSE. Never writes. Missing table key
    is UNKNOWN. A sealed run_id fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if type(run_id) is not str:
        if run_id is None:
            return None
        raise FailClosedError(f"run_id must be a str or None: {run_id!r}")
    if not run_id.strip():
        raise FailClosedError("run_id is empty")
    folded = run_id.strip().lower().replace("-", "_")
    if folded in _SEALED_ACTIONS:
        raise FailClosedError(
            f"run_id names a sealed send/ready state: {run_id!r}")
    text = run_id.strip()
    if text not in table:
        return None
    pinned = table[text]
    klass = classify_action(pinned)
    if klass == "UNKNOWN":
        raise FailClosedError(
            f"pinned action drifted to UNKNOWN: {pinned!r}")
    return klass


def pin_limit(
    table: MutableMapping[str, str],
    bind: ScopeBind,
) -> str:
    """Record (run_id → action) at most once per distinct action.

    First pin → limited. Same pair again → already_limited.
    Different action on the same run_id fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, ScopeBind):
        raise FailClosedError(f"bind must be a ScopeBind: {bind!r}")
    # Re-bind so a hand-built object cannot sneak a sealed name.
    checked = bind_scope(bind.action, bind.run_id)
    existing = peek_limit(table, checked.run_id)
    if existing is None:
        table[checked.run_id] = checked.action
        return LIMITED
    if existing == checked.action:
        return ALREADY_LIMITED
    raise FailClosedError(
        f"action_collision: run_id {checked.run_id!r} pinned "
        f"{existing!r}, refused {checked.action!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: ScopeBind,
) -> Optional[bool]:
    """True when bind.action disagrees with a pinned action.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, ScopeBind):
        raise FailClosedError(f"bind must be a ScopeBind: {bind!r}")
    existing = peek_limit(table, bind.run_id)
    if existing is None:
        return None
    return existing != bind.action
