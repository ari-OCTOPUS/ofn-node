"""Pin that a classified destination cannot leave the node.

A pin is not a send. OUTBOX is staged, not emptied. LOOPBACK is
local, not a customer path. UNKNOWN stays UNKNOWN (None), not
FALSE. external and sealed send/ready names fail closed — they
are not pinned as granted.

``pin_deny`` continues under HALT (a pin is not a START).
``pin_allows_leave`` is structurally False for every admitted
class; it never returns True.

campaign_envelope_ready is structurally distinct from
send_authorized; both are refused as pin targets.

Distinct from send_fence.admit_send (state names) and from
egress_class.admit_leave (the START). Not wired into the
run store.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Optional

from .egress_class import (
    CLASSES,
    EgressClass,
    classify_dest,
    grants_send as _class_grants_send,
)
from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

DENIED = "DENIED"
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
    """A deny pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not a pin."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A pin is not a rename of authorized."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
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


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def wires_into_run_store() -> bool:
    """Structurally False. This module is not imported by the store."""
    return False


def pin_allows_leave() -> bool:
    """Structurally False. No classified dest is a leave grant."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name) or is_sealed_tool_name(name):
        return True
    folded = _fold(name)
    return folded in {s.replace("-", "_") for s in _SEALED}


def pin_deny(target: object) -> Optional[str]:
    """Pin a classified dest or an EgressClass as DENIED.

    None / UNKNOWN → None (UNKNOWN, not FALSE).
    OUTBOX / LOOPBACK / their dest names → DENIED.
    external / sealed send/ready names fail closed.
    A Python bool is refused.
    """
    if target is None:
        return None
    if isinstance(target, bool):
        raise FailClosedError(f"pin target must be a name or class: {target!r}")
    if isinstance(target, EgressClass):
        if target.grants_send or _class_grants_send():
            raise FailClosedError("pinned class cannot grant send")
        if target.klass == "UNKNOWN":
            return None
        if target.klass in CLASSES:
            return DENIED
        raise FailClosedError(f"unknown class cannot be pinned: {target.klass!r}")
    if isinstance(target, str):
        if _is_sealed(target):
            raise FailClosedError(
                "sealed send/ready name is not a deny pin")
        folded = _fold(target)
        if folded in {"unknown", "none"}:
            return None
        if folded in {"outbox", "loopback", "denied"}:
            return DENIED
        if folded == "external":
            raise FailClosedError(
                "external cannot be pinned as granted — known refusal")
        classified = classify_dest(target)
        if classified.klass == "UNKNOWN":
            return None
        return DENIED
    raise FailClosedError(f"pin target must be a name or class: {target!r}")
