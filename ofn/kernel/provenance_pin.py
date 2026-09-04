"""Provenance pin — kernel-pure containment of a lineage role.

lineage_class classifies a node as root / successor / orphan /
unknown. This pin is the second witness: may that role be treated
as a contained edge?

``genesis`` is a root. ``contained`` is a successor whose parent
was already named. ``unbound`` is an orphan. ``unknown`` stays
unknown — it is not FALSE and it is not a grant.

A sealed send/ready name is never a node_id and never a parent_id.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused as ``sealed_effect``.

Pinning a contained edge is not ``send_authorized``,
``quote_sent``, or ``campaign_envelope_ready``. Ready is not
authorized. An orphan is not a send.

HALT stops STARTS. This pin has no halt parameter: in-flight
containment checks must still work so recovery does not need
the owner.

Distinct from lineage_class (admission), hash_chain (byte digest),
event_id (evt- uniqueness), contract_pin (cited sha256), and
artifact_ref. Not wired into the run store.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .lineage_class import INTENTS, ROLES

# Closed vocabularies. Widen only with a test.
FAMILIES = frozenset({"genesis", "contained", "unbound", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "unbound_orphan",
    "unknown_role",
    "role_intent_mismatch",
    "self_parent",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

_FAMILY_FOR_ROLE = {
    "root": "genesis",
    "successor": "contained",
    "orphan": "unbound",
    "unknown": "unknown",
}


def grants_send() -> bool:
    """A provenance pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_contained() -> bool:
    """Structurally False. Unknown is not a contained edge."""
    return False


def orphan_is_contained() -> bool:
    """Structurally False. An orphan is unbound, not contained."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Pinning a role is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def pin_family(role: object) -> str:
    """Map a lineage role onto a closed family. Unknown roles fail closed."""
    name = _require_name(role, what="role")
    if name not in ROLES:
        raise FailClosedError(
            f"unknown role is not a refusal and not a grant: {name!r}")
    return _FAMILY_FOR_ROLE[name]


def pin_allows(role: object, *, intended: object) -> bool:
    """True only for genesis+mint or contained+succeed.

    Orphan and unknown never allow. Observe never allows a pin
    grant — observe is read-side and does not claim containment.
    """
    family = pin_family(role)
    intent = _require_name(intended, what="intended")
    if intent not in INTENTS:
        raise FailClosedError(
            f"unknown intended is not a refusal and not a grant: {intent!r}")
    if family == "genesis" and intent == "mint":
        return True
    if family == "contained" and intent == "succeed":
        return True
    return False


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {_fold(s) for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


@dataclass(frozen=True)
class ProvenancePin:
    """The containment pin. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    family: str
    role: str
    intended: str
    node_id: str
    parent_id: Optional[str]
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "ProvenancePin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a provenance pin is not a send")
        if self.family not in FAMILIES:
            raise FailClosedError(
                f"unknown family is not a refusal and not a grant: "
                f"{self.family!r}")
        if self.role not in ROLES:
            raise FailClosedError(f"unknown or missing role: {self.role!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        object.__setattr__(self, "node_id", _require_name(self.node_id, what="node_id"))
        if self.parent_id is not None:
            object.__setattr__(
                self, "parent_id",
                _require_name(self.parent_id, what="parent_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed pin must not carry a reason: {self.reason!r}")
            if self.family not in {"genesis", "contained"}:
                raise FailClosedError(
                    "ProvenancePin cannot allow unbound or unknown")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if (
            _is_sealed(self.node_id)
            or _is_sealed(self.parent_id)
            or _is_sealed(self.role)
            or _is_sealed(self.intended)
            or _is_sealed(self.family)
        ):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "ProvenancePin cannot grant or mis-label a sealed "
                    "send/ready name")


def pin_provenance(
    *,
    role: object,
    intended: object,
    node_id: object,
    parent_id: object = None,
) -> ProvenancePin:
    """Pin a lineage role as genesis / contained / unbound / unknown.

    ``role``, ``intended``, and ``node_id`` are required names.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as contained.

    A sealed send/ready name is a known refusal (``sealed_effect``).
    An orphan is ``unbound_orphan``. An unknown role is
    ``unknown_role`` (not FALSE). A self-parent is ``self_parent``.
    A role/intent mismatch is ``role_intent_mismatch``.

    Signature is sealed: no ``resend``, no ``send_authorized``,
    no ``halt``. Tests lock the parameter list; the kernel does
    not import inspect.
    """
    raw_role = _require_name(role, what="role")
    raw_intent = _require_name(intended, what="intended")
    raw_node = _require_name(node_id, what="node_id")
    if parent_id is not None:
        raw_parent: Optional[str] = _require_name(parent_id, what="parent_id")
    else:
        raw_parent = None

    if (
        _is_sealed(raw_role)
        or _is_sealed(raw_intent)
        or _is_sealed(raw_node)
        or _is_sealed(raw_parent)
    ):
        recorded_role = raw_role if raw_role in ROLES else "unknown"
        recorded_intent = raw_intent if raw_intent in INTENTS else "observe"
        return ProvenancePin(
            allowed=False,
            reason="sealed_effect",
            family="unknown",
            role=recorded_role,
            intended=recorded_intent,
            node_id=raw_node,
            parent_id=raw_parent,
        )

    if raw_role not in ROLES:
        raise FailClosedError(
            f"unknown role is not a refusal and not a grant: {raw_role!r}")
    if raw_intent not in INTENTS:
        raise FailClosedError(
            f"unknown intended is not a refusal and not a grant: {raw_intent!r}")

    family = pin_family(raw_role)

    if raw_parent is not None and raw_parent == raw_node:
        return ProvenancePin(
            allowed=False,
            reason="self_parent",
            family=family,
            role=raw_role,
            intended=raw_intent,
            node_id=raw_node,
            parent_id=raw_parent,
        )

    if family == "unbound":
        return ProvenancePin(
            allowed=False,
            reason="unbound_orphan",
            family=family,
            role=raw_role,
            intended=raw_intent,
            node_id=raw_node,
            parent_id=raw_parent,
        )
    if family == "unknown":
        return ProvenancePin(
            allowed=False,
            reason="unknown_role",
            family=family,
            role=raw_role,
            intended=raw_intent,
            node_id=raw_node,
            parent_id=raw_parent,
        )
    if not pin_allows(raw_role, intended=raw_intent):
        return ProvenancePin(
            allowed=False,
            reason="role_intent_mismatch",
            family=family,
            role=raw_role,
            intended=raw_intent,
            node_id=raw_node,
            parent_id=raw_parent,
        )
    return ProvenancePin(
        allowed=True,
        reason=None,
        family=family,
        role=raw_role,
        intended=raw_intent,
        node_id=raw_node,
        parent_id=raw_parent,
    )
