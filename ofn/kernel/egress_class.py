"""Classify a destination class. Classification is not a send.

Closed destinations:

  outbox   — staging only; emptying is an owner act
  loopback — this-host collection; not a customer path
  external — known refusal (not a missing class)

Missing is UNKNOWN, not FALSE. An unknown string is not classified
as FALSE — it fails closed. A sealed send/ready name is a known
refusal, not an unknown destination.

``admit_leave`` is a START: HALT refuses it. ``classify_dest`` is
collection and continues under HALT so recovery does not need the
owner.

campaign_envelope_ready is structurally distinct from
send_authorized; both are refused as destinations.

Distinct from send_fence (revenue *state* names), write_fence
(durable *surfaces*), and adapters.outbox. Not wired into the
run store.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name, payload_forbidden_effect

DESTINATIONS = frozenset({"outbox", "loopback", "external"})
CLASSES = frozenset({"OUTBOX", "LOOPBACK", "UNKNOWN"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

_CLASS_BY_DEST = {
    "outbox": "OUTBOX",
    "loopback": "LOOPBACK",
}


def grants_send() -> bool:
    """A destination class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def halt_blocks_leave() -> bool:
    """Structurally True. admit_leave is a START."""
    return True


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A class is not a rename of authorized."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A class is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a dest is not an external effect."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def wires_into_run_store() -> bool:
    """Structurally False. This module is not imported by the store."""
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


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


@dataclass(frozen=True)
class EgressClass:
    """One destination classification. ``grants_send`` is structurally False."""

    klass: str
    dest: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "EgressClass cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a class is not a send")
        if self.klass not in CLASSES:
            raise FailClosedError(f"unknown egress class: {self.klass!r}")
        object.__setattr__(self, "dest", _require_name(self.dest, what="dest"))
        if _is_sealed(self.dest) or _is_sealed(self.klass):
            raise FailClosedError(
                "EgressClass cannot carry a sealed send/ready name")
        if self.klass == "UNKNOWN" and self.dest != "UNKNOWN":
            raise FailClosedError(
                "UNKNOWN class must record dest=UNKNOWN, not a silent dest")


def classify_dest(
    dest: object,
    *,
    kind: object = None,
    payload: Optional[Mapping[str, object]] = None,
) -> EgressClass:
    """Classify one destination.

    ``dest`` None or kind ``timeout`` → UNKNOWN (not FALSE, not a writer).
    ``outbox`` / ``loopback`` → named class.
    ``external`` is a known refusal, not an unknown.
    Sealed send/ready names refuse.
    Unknown strings fail closed — they are not FALSE.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    ``halt`` is not a parameter here; collection continues.
    """
    if payload is not None:
        if isinstance(payload, (str, bytes, bytearray)) or not isinstance(payload, Mapping):
            raise FailClosedError(f"payload must be a mapping: {payload!r}")
        smuggled = payload_forbidden_effect(payload)
        if smuggled is not None:
            raise FailClosedError(
                f"payload smuggles forbidden effect name {smuggled!r}")

    if kind is not None:
        kind_name = _require_name(kind, what="kind")
        if _is_sealed(kind_name):
            raise FailClosedError(
                "sealed send/ready name is not an egress kind")
        if kind_name == "timeout":
            return EgressClass(klass="UNKNOWN", dest="UNKNOWN")
        if kind_name != "direct":
            raise FailClosedError(
                f"unknown egress kind is not FALSE: {kind_name!r}")

    if dest is None:
        return EgressClass(klass="UNKNOWN", dest="UNKNOWN")

    dest_name = _require_name(dest, what="dest")
    if _is_sealed(dest_name):
        raise FailClosedError(
            "sealed send/ready name is not a destination")

    folded = _fold(dest_name)
    if folded == "external":
        raise FailClosedError(
            "external is a known refusal — not a missing class and "
            "not a send")
    if folded not in _CLASS_BY_DEST:
        raise FailClosedError(
            f"unknown destination is not FALSE: {dest_name!r}")
    return EgressClass(klass=_CLASS_BY_DEST[folded], dest=folded)


def admit_leave(
    dest: object,
    *,
    halt: object = False,
    kind: object = None,
    payload: Optional[Mapping[str, object]] = None,
) -> Optional[bool]:
    """START: may this destination leave the node?

    True is unreachable. HALT refuses (this is a START).
    UNKNOWN dest → None (not FALSE).
    OUTBOX / LOOPBACK → False (class known, leave denied).
    external / sealed names fail closed.
    A Python bool dest is refused.
    """
    if halt is True:
        raise FailClosedError(
            "HALT stops STARTS — admit_leave is a START")
    if halt is not False:
        raise FailClosedError(f"halt must be a bool False or True: {halt!r}")

    classified = classify_dest(dest, kind=kind, payload=payload)
    if classified.klass == "UNKNOWN":
        return None
    if classified.klass in {"OUTBOX", "LOOPBACK"}:
        return False
    raise FailClosedError(
        f"admit_leave cannot grant {classified.klass!r}")
