"""Pin a TaskBind so the intent cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (run_id → intent). The same pair
again is already_pinned. A different intent on the same run_id
fails closed as intent_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized.

Not wired into run_store.py. HALT stops STARTS, not a pin.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .task_bind import (
    MINT,
    TaskBind,
    bind_task,
    classify_intent,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED_INTENTS = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """An intent pin never authorizes a send. Structurally False."""
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


def pin_allows_send(bind: TaskBind) -> bool:
    """Structurally False. Even a mint bind is not send_authorized."""
    if not isinstance(bind, TaskBind):
        raise FailClosedError(f"bind must be a TaskBind: {bind!r}")
    return False


def pin_allows_mint(bind: TaskBind) -> bool:
    """True only when the pinned intent is mint.

    This is not a grant of minting and not send_authorized.
    HALT still stops the factory START.
    """
    if not isinstance(bind, TaskBind):
        raise FailClosedError(f"bind must be a TaskBind: {bind!r}")
    return bind.intent == MINT


def peek_pin(table: Mapping[str, str], run_id: object) -> Optional[str]:
    """Return the pinned intent or None.

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
    if folded in _SEALED_INTENTS:
        raise FailClosedError(
            f"run_id names a sealed send/ready state: {run_id!r}")
    text = run_id.strip()
    if text not in table:
        return None
    pinned = table[text]
    klass = classify_intent(pinned)
    if klass == "UNKNOWN":
        raise FailClosedError(
            f"pinned intent drifted to UNKNOWN: {pinned!r}")
    return klass


def pin_intent(
    table: MutableMapping[str, str],
    bind: TaskBind,
) -> str:
    """Record (run_id → intent) at most once per distinct intent.

    First pin → pinned. Same pair again → already_pinned.
    Different intent on the same run_id fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, TaskBind):
        raise FailClosedError(f"bind must be a TaskBind: {bind!r}")
    # Re-bind so a hand-built object cannot sneak a sealed name.
    checked = bind_task(bind.intent, bind.run_id)
    existing = peek_pin(table, checked.run_id)
    if existing is None:
        table[checked.run_id] = checked.intent
        return PINNED
    if existing == checked.intent:
        return ALREADY_PINNED
    raise FailClosedError(
        f"intent_collision: run_id {checked.run_id!r} pinned "
        f"{existing!r}, refused {checked.intent!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: TaskBind,
) -> Optional[bool]:
    """True when bind.intent disagrees with a pinned intent.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, TaskBind):
        raise FailClosedError(f"bind must be a TaskBind: {bind!r}")
    existing = peek_pin(table, bind.run_id)
    if existing is None:
        return None
    return existing != bind.intent
