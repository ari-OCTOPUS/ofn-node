"""Pin a CascadeBind so isolated cannot be retconned into cascade.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(stop → family:scope:child_count).
The same triple again is already_pinned. A different
family, declared scope, or count on the same stop fails
closed as stop_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from halt.py, halt_ops, halt_latch, quorum/seat,
later_hold/scoped_authz, receipts, and dedup.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .cascade_class import (
    CASCADE,
    ISOLATED,
    RECORD,
    CascadeBind,
    bind_cascade,
    classify_intent,
    classify_propagation,
)
from .errors import FailClosedError

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A stop pin never authorizes a send. Structurally False."""
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


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def cascade_is_authorized() -> bool:
    """Structurally False. cascade is a family, not send_authorized."""
    return False


def children_do_not_promote() -> bool:
    """Structurally True. Children cannot retcon isolated into cascade."""
    return True


def pin_allows_send(bind: CascadeBind) -> bool:
    """Structurally False. Even a record bind is not send_authorized."""
    if not isinstance(bind, CascadeBind):
        raise FailClosedError(f"bind must be a CascadeBind: {bind!r}")
    return False


def pin_allows_record(bind: CascadeBind) -> bool:
    """True only when the pinned intent is record and family is
    isolated or cascade.

    Both families are valid scopes. This is not a grant of
    sending and not send_authorized. HALT still stops the
    factory START.
    """
    if not isinstance(bind, CascadeBind):
        raise FailClosedError(f"bind must be a CascadeBind: {bind!r}")
    return bind.intent == RECORD and bind.family in {ISOLATED, CASCADE}


def _encode(bind: CascadeBind) -> str:
    return f"{bind.family}:{bind.scope}:{bind.child_count}"


def _refuse_sealed_stop(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"stop names a sealed send/ready state: {value!r}")


def peek_stop(table: Mapping[str, str], stop: object) -> Optional[str]:
    """Return the pinned encoding or None.

    None is UNKNOWN, not FALSE. Never writes. Missing table key
    is UNKNOWN. A sealed stop fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if type(stop) is not str:
        if stop is None:
            return None
        raise FailClosedError(f"stop must be a str or None: {stop!r}")
    if not stop.strip():
        raise FailClosedError("stop is empty")
    _refuse_sealed_stop(stop)
    text = stop.strip()
    if text not in table:
        return None
    pinned = table[text]
    if type(pinned) is not str or pinned.count(":") != 2:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    family, scope_text, count_text = pinned.split(":")
    if family not in {ISOLATED, CASCADE}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if scope_text not in {ISOLATED, CASCADE}:
        raise FailClosedError(f"pinned scope drifted: {scope_text!r}")
    if not count_text.isdigit():
        raise FailClosedError(f"pinned count drifted: {pinned!r}")
    return pinned


def pin_stop(
    table: MutableMapping[str, str],
    bind: CascadeBind,
) -> str:
    """Record (stop → family:scope:child_count) at most once.

    First pin → pinned. Same triple again → already_pinned.
    Different family, declared scope, or count on the same
    stop fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, CascadeBind):
        raise FailClosedError(f"bind must be a CascadeBind: {bind!r}")
    checked = bind_cascade(
        bind.intent,
        bind.scope,
        bind.child_count,
        stop=bind.stop,
    )
    if (
        checked.family != bind.family
        or checked.scope != bind.scope
        or checked.child_count != bind.child_count
    ):
        raise FailClosedError(
            "CascadeBind drifted from re-bind: "
            f"have family={bind.family!r} scope={bind.scope!r} "
            f"child_count={bind.child_count!r}")
    existing = peek_stop(table, checked.stop)
    encoded = _encode(checked)
    if existing is None:
        table[checked.stop] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"stop_collision: stop {checked.stop!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: CascadeBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, CascadeBind):
        raise FailClosedError(f"bind must be a CascadeBind: {bind!r}")
    existing = peek_stop(table, bind.stop)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    scope: object,
    child_count: object,
    *,
    stop: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing scope/child_count/intent/stop or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if (
        intent is None
        or scope is None
        or child_count is None
        or stop is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_propagation(scope, child_count, timeout=False) is None:
        return None
    return pin_stop(
        table,
        bind_cascade(intent, scope, child_count, stop=stop),
    )
