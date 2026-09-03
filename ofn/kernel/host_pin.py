"""Host pin — bind a presence class to one node without promoting.

A pin records (body_class, node_id, vantage). Vantage is
``this_host_only``. ``system_wide`` is a known refusal
(``promotion_refused``): one node cannot mint a fleet-wide miss.

This module does not take a second node_id. Two-node promotion is
an owner decision, not a silent default.

A pin never grants a send. ``campaign_envelope_ready`` cannot be
pinned into ``send_authorized``. Binding a host is not an
``EXECUTION_RECEIPT`` and is not a chain tip.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not invent a body or a node.

Not wired into the run store. Pinning a host is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: pinning a
host is not a run start.

Kernel purity: dataclasses + typing + re. No hashlib of bodies,
no I/O, no clock, no now().
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .body_class import (
    CLASSES as BODY_CLASSES,
    admit_body,
    classify_body,
)
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
PIN_CLASSES = frozenset({"BOUND", "UNKNOWN"})
VANTAGES = frozenset({"this_host_only"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "missing_claim",
    "promotion_refused",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

# Abstract node token. Not an address, not a secret, not a send.
_NODE_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def grants_send() -> bool:
    """A host pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not a pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A pin is not an external effect."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This pin is not wired into the store."""
    return False


def invents_second_node() -> bool:
    """Structurally False. A pin records one node; it does not mint a peer."""
    return False


def promotes_to_system_wide() -> bool:
    """Structurally False. this_host_only stays this_host_only."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A pin does not consume a key."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if type(name) is not str:
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {s.replace("-", "_") for s in _SEALED}


def _check_node_id(node_id: object) -> Optional[str]:
    if node_id is None:
        return None
    if type(node_id) is not str:
        raise FailClosedError(f"node_id must be a str or None: {node_id!r}")
    if not node_id.strip():
        raise FailClosedError("node_id is empty")
    if _is_sealed(node_id):
        raise FailClosedError(
            f"node_id names a sealed send/ready state: {node_id!r}")
    if not _NODE_ID_RE.match(node_id):
        raise FailClosedError(f"node_id is not a closed token: {node_id!r}")
    return node_id


def classify_pin(location: object, node_id: object) -> Optional[str]:
    """BOUND or UNKNOWN (None). Missing either side is UNKNOWN.

    Sealed send/ready names fail closed — they are not a pin class.
    A body_missing claim still fails closed (shape / authority error).
    Present-but-bad tokens fail closed.
    """
    if location is None or node_id is None:
        return None
    body = classify_body(location)
    node = _check_node_id(node_id)
    if body is None or node is None:
        return None
    if body not in BODY_CLASSES:
        raise FailClosedError("body class drifted")
    if body == "UNKNOWN":
        return None
    return "BOUND"


@dataclass(frozen=True)
class HostPin:
    """One body+node binding. Frozen so a later write cannot silently
    retcon the pin into send_authorized or system_wide.
    """

    location: Optional[str]
    node_id: Optional[str]
    vantage: str
    body_class: str
    pin_class: str
    allowed: bool
    reason: Optional[str]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "HostPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a host pin is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be exact bool: {self.timed_out!r}")
        if self.pin_class not in PIN_CLASSES:
            raise FailClosedError(
                f"unknown pin class: {self.pin_class!r}")
        if self.body_class not in BODY_CLASSES:
            raise FailClosedError(
                f"unknown body class: {self.body_class!r}")
        if self.vantage not in VANTAGES and self.reason != "promotion_refused":
            raise FailClosedError(
                f"unknown vantage: {self.vantage!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed pin must not carry a reason: {self.reason!r}")
            if self.vantage != "this_host_only":
                raise FailClosedError(
                    "allowed pin vantage must be this_host_only")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if self.node_id is not None:
            if type(self.node_id) is not str:
                raise FailClosedError("node_id must be a str or None")
            if _is_sealed(self.node_id):
                if self.allowed or self.reason != "sealed_effect":
                    raise FailClosedError(
                        "sealed name may appear only as a sealed_effect "
                        "subject")
            elif not _NODE_ID_RE.match(self.node_id):
                raise FailClosedError(
                    f"node_id must be a closed token: {self.node_id!r}")
        if self.location is not None:
            if type(self.location) is not str:
                raise FailClosedError("location must be a str or None")
            if _is_sealed(self.location):
                if self.allowed or self.reason != "sealed_effect":
                    raise FailClosedError(
                        "sealed name may appear only as a sealed_effect "
                        "subject")
        if self.pin_class == "BOUND":
            if (
                self.location is None
                or self.node_id is None
                or self.body_class not in {"ON_THIS_HOST", "NOT_ON_THIS_HOST"}
            ):
                raise FailClosedError(
                    "BOUND requires a located body and a node_id")
            if self.timed_out:
                raise FailClosedError("timed-out pin cannot be BOUND")
        if self.pin_class == "UNKNOWN" and not self.timed_out:
            if (
                self.allowed
                and self.location is not None
                and self.node_id is not None
                and not _is_sealed(self.location)
                and self.body_class in {"ON_THIS_HOST", "NOT_ON_THIS_HOST"}
            ):
                raise FailClosedError(
                    "located body + node cannot be UNKNOWN without timeout")


def pin_host(
    location: object,
    node_id: object,
    *,
    vantage: object = "this_host_only",
    timed_out: bool = False,
) -> HostPin:
    """Pin a presence class to one node.

    Missing location or node_id is UNKNOWN and admitted. A sealed
    send/ready name on either side is a known refusal
    (``sealed_effect``). A one-vantage ``body_missing`` claim is
    ``missing_claim``. ``system_wide`` vantage is
    ``promotion_refused``. Timeout forces UNKNOWN and does not
    invent a second node.

    Signature is sealed: no ``halt``, no ``send_authorized``, no
    ``resend``. Tests lock the parameter list.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be exact bool: {timed_out!r}")
    if type(vantage) is not str:
        raise FailClosedError(f"vantage must be a str: {vantage!r}")

    if _is_sealed(location) or _is_sealed(node_id):
        sealed = location if _is_sealed(location) else node_id
        if type(sealed) is not str:
            raise FailClosedError(f"sealed pin side must be a str: {sealed!r}")
        loc_rec = location if type(location) is str else None
        node_rec = node_id if type(node_id) is str else None
        return HostPin(
            location=loc_rec,
            node_id=node_rec,
            vantage="this_host_only",
            body_class="UNKNOWN",
            pin_class="UNKNOWN",
            allowed=False,
            reason="sealed_effect",
            timed_out=timed_out,
        )

    body_dec = admit_body(location, timed_out=False)
    if not body_dec.allowed:
        return HostPin(
            location=body_dec.location,
            node_id=node_id if type(node_id) is str else None,
            vantage="this_host_only",
            body_class="UNKNOWN",
            pin_class="UNKNOWN",
            allowed=False,
            reason=body_dec.reason,
            timed_out=timed_out,
        )

    node = _check_node_id(node_id)

    folded_vantage = _fold(vantage)
    if folded_vantage == "system_wide":
        return HostPin(
            location=body_dec.location,
            node_id=node,
            vantage="system_wide",
            body_class="UNKNOWN",
            pin_class="UNKNOWN",
            allowed=False,
            reason="promotion_refused",
            timed_out=timed_out,
        )
    if folded_vantage not in VANTAGES:
        raise FailClosedError(f"vantage is not a closed token: {vantage!r}")

    if location is None or node is None:
        return HostPin(
            location=body_dec.location,
            node_id=node,
            vantage="this_host_only",
            body_class="UNKNOWN",
            pin_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=timed_out,
        )

    if timed_out:
        return HostPin(
            location=body_dec.location,
            node_id=node,
            vantage="this_host_only",
            body_class="UNKNOWN",
            pin_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=True,
        )

    klass = classify_pin(location, node)
    if klass is None:
        return HostPin(
            location=body_dec.location,
            node_id=node,
            vantage="this_host_only",
            body_class="UNKNOWN",
            pin_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=False,
        )
    return HostPin(
        location=body_dec.location,
        node_id=node,
        vantage="this_host_only",
        body_class=body_dec.body_class,
        pin_class=klass,
        allowed=True,
        reason=None,
        timed_out=False,
    )


def try_pin(location: object, node_id: object) -> Optional[HostPin]:
    """Missing either side is UNKNOWN (None). Present-but-bad fails closed."""
    if location is None or node_id is None:
        return None
    return pin_host(location, node_id)
