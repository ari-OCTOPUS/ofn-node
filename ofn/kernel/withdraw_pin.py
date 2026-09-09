"""Pin a RevokeBind so a withdrawn ready hold cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records
(slot → family:intent:subject_kind:subject).
The same quadruple again is already_pinned. A different
family, intent, subject_kind, or subject on the same slot
fails closed as withdraw_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later withdraw supersedes
an older ready hold. A later disarm supersedes an older
authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from send_fence, campaign_bind, void/cancel,
hold/disarm, later_hold/scoped_authz, and close_gate.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional

from .errors import FailClosedError
from .revoke_class import (
    CLASSIFY,
    HELD,
    ISSUE,
    OBSERVE,
    READY,
    REVOKE,
    RUN,
    WITHDRAWN,
    RevokeBind,
    bind_revoke,
    classify_family,
    classify_intent,
    classify_subject,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEND_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
})


def grants_send() -> bool:
    """A withdraw pin never authorizes a send. Structurally False."""
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
    """Structurally False. Ready stays ready, or is withdrawn."""
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


def later_withdraw_supersedes() -> bool:
    """Structurally True. A later withdraw beats an older ready hold."""
    return True


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def withdrawn_is_authorized() -> bool:
    """Structurally False. A withdrawn pin is not send_authorized."""
    return False


def pin_allows_send(bind: RevokeBind) -> bool:
    """Structurally False. Even an issue bind is not send_authorized."""
    if not isinstance(bind, RevokeBind):
        raise FailClosedError(f"bind must be a RevokeBind: {bind!r}")
    return False


def pin_allows_revoke(bind: RevokeBind) -> bool:
    """True only when the pinned intent is revoke and family is held.

    A held ready may still be withdrawn. withdrawn family has
    already been withdrawn. This is not a grant of sending and
    not send_authorized. HALT still stops the issue START.
    """
    if not isinstance(bind, RevokeBind):
        raise FailClosedError(f"bind must be a RevokeBind: {bind!r}")
    return bind.intent == REVOKE and bind.family == HELD


def _encode(bind: RevokeBind) -> str:
    return (
        f"{bind.family}:{bind.intent}:{bind.subject_kind}:{bind.subject}"
    )


def _refuse_send_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEND_SEALED}:
        raise FailClosedError(
            f"slot names a sealed send state: {value!r}")


def peek_withdraw(table: Mapping[str, str], slot: object) -> Optional[str]:
    """Return the pinned encoding or None.

    None is UNKNOWN, not FALSE. Never writes. Missing table key
    is UNKNOWN. A send-sealed slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if type(slot) is not str:
        if slot is None:
            return None
        raise FailClosedError(f"slot must be a str or None: {slot!r}")
    if not slot.strip():
        raise FailClosedError("slot is empty")
    _refuse_send_slot(slot)
    text = slot.strip()
    if text not in table:
        return None
    pinned = table[text]
    if type(pinned) is not str or pinned.count(":") != 3:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    family, intent, subject_kind, subject = pinned.split(":")
    if family not in {HELD, WITHDRAWN}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if intent not in {ISSUE, REVOKE, CLASSIFY, OBSERVE}:
        raise FailClosedError(f"pinned intent drifted: {intent!r}")
    if subject_kind not in {READY, RUN}:
        raise FailClosedError(
            f"pinned subject_kind drifted: {subject_kind!r}")
    if not subject:
        raise FailClosedError(f"pinned subject missing: {pinned!r}")
    return pinned


def pin_withdraw(
    table: MutableMapping[str, str],
    bind: RevokeBind,
) -> str:
    """Record (slot → family:intent:subject_kind:subject) at most once.

    First pin → pinned. Same quadruple again → already_pinned.
    Different family, intent, subject_kind, or subject on the
    same slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, RevokeBind):
        raise FailClosedError(f"bind must be a RevokeBind: {bind!r}")
    checked = bind_revoke(
        bind.intent,
        bind.subject if bind.subject_kind == RUN else READY,
        withdrawn=bind.family == WITHDRAWN,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.intent != bind.intent
        or checked.subject_kind != bind.subject_kind
        or checked.subject != bind.subject
    ):
        raise FailClosedError(
            "RevokeBind drifted from re-bind: "
            f"have family={bind.family!r} intent={bind.intent!r} "
            f"subject_kind={bind.subject_kind!r} subject={bind.subject!r}")
    existing = peek_withdraw(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"withdraw_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: RevokeBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, RevokeBind):
        raise FailClosedError(f"bind must be a RevokeBind: {bind!r}")
    existing = peek_withdraw(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    subject: object,
    *,
    withdrawn: object,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing sides or timeout is UNKNOWN (None).

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
        or subject is None
        or withdrawn is None
        or slot is None
    ):
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_subject(subject) is None:
        return None
    if classify_family(withdrawn, timeout=False) is None:
        return None
    return pin_withdraw(
        table,
        bind_revoke(
            intent, subject, withdrawn=withdrawn, slot=slot),
    )
