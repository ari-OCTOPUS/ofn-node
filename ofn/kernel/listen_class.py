"""Listen class — kernel-pure classifier for a proposed bind.

Adapters can open a socket. This module is the second witness: may
that bind START, or is the address only being named?

Closed families:

  loopback   → 127.0.0.1 or ::1
  wildcard   → 0.0.0.0 or :: or *
  lan        → any other well-formed address
  unknown    → unreadable / unclassifiable. Never a silent skip.

``bind`` is a START. HALT refuses it. ``classify`` and ``observe``
are not STARTS — HALT does not block naming an address so recovery
does not need the owner.

A wildcard is never local and is never admitted as a bind.
A LAN address is an observation, not a grant to bind.
A missing LAN probe is inference, not proof that loopback is
absent. A timeout is UNKNOWN; it does not prove concurrent
writing and it does not prove an API is missing.

A sealed send/ready name is never an address and never an intent.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

Not wired into the run store or any adapter. Admitting a loopback
bind is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: dataclasses + re + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"bind", "classify", "observe"})
FAMILIES = frozenset({"loopback", "wildcard", "lan", "unknown"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
PROBES = frozenset({"open", "closed", "timeout", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "sealed_wildcard",
    "lan_not_local",
    "unknown_address",
    "halt_active",
    "unknown_probe",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

LOOPBACK_ADDRS = frozenset({"127.0.0.1", "::1"})
WILDCARD_ADDRS = frozenset({"0.0.0.0", "::", "*"})

_IPV4_RE = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")


def grants_send() -> bool:
    """A listen class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not classify/observe."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A bind verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def timeout_proves_absent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not 'API missing'."""
    return False


def missing_lan_proves_absent() -> bool:
    """Structurally False. Missing LAN is not loopback absence."""
    return False


def wildcard_is_local() -> bool:
    """Structurally False. 0.0.0.0 is not loopback."""
    return False


def lan_is_local() -> bool:
    """Structurally False. A LAN address is not a local bind grant."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming an address is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


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


def _require_member(value: object, *, what: str, allowed: frozenset[str]) -> str:
    name = _require_name(value, what=what)
    if name not in allowed:
        raise FailClosedError(
            f"unknown {what} is not a refusal and not a grant: {name!r}")
    return name


def _ipv4_octets_ok(address: str) -> bool:
    parts = address.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or (len(part) > 1 and part.startswith("0")):
            return False
        n = int(part)
        if n < 0 or n > 255:
            return False
    return True


def classify_family(address: object) -> str:
    """Name the address family. Unknown is unknown, not lan.

    Exact literals win. A well-formed IPv4 that is not loopback or
    wildcard is lan. A string with ':' that is not ::1 or :: is lan.
    Everything else is unknown. Sealed send/ready names fail closed.
    """
    name = _require_name(address, what="address")
    if _is_sealed(name):
        raise FailClosedError(
            f"address names a sealed send/ready state: {name!r}")
    if name in LOOPBACK_ADDRS:
        return "loopback"
    if name in WILDCARD_ADDRS:
        return "wildcard"
    if _IPV4_RE.match(name) is not None and _ipv4_octets_ok(name):
        return "lan"
    if ":" in name:
        return "lan"
    return "unknown"


def classify_status(*, probe: str, timed_out: bool) -> str:
    """Derive the listen-row status. Timeout outranks probe.

    A timeout is UNKNOWN even when the probe says open or closed.
    That is the load-bearing rule: timeout does not prove a race
    and does not prove an API is missing.
    """
    if timed_out:
        return "UNKNOWN"
    if probe == "timeout" or probe == "unknown":
        return "UNKNOWN"
    if probe == "closed":
        return "SUSPECTED"
    if probe == "open":
        return "VERIFIED"
    raise FailClosedError(
        f"unknown probe is not a refusal and not a grant: {probe!r}")


@dataclass(frozen=True)
class ListenDecision:
    """The listen-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    family: str
    intended: str
    address: str
    status: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "ListenDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a listen class is not a send")
        if self.family not in FAMILIES:
            raise FailClosedError(
                f"unknown listen family is not a refusal and not a grant: "
                f"{self.family!r}")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown listen status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(
            self, "address", _require_name(self.address, what="address"))
        if _is_sealed(self.address) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "ListenDecision cannot grant or mis-label a sealed "
                    "send/ready name")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed listen must not carry a reason: {self.reason!r}")
            if self.intended == "bind" and self.family != "loopback":
                raise FailClosedError(
                    "ListenDecision cannot allow a bind unless loopback")
            if self.intended == "bind" and self.status == "UNKNOWN":
                raise FailClosedError(
                    "ListenDecision cannot allow a bind while UNKNOWN")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")


def admit_listen(
    *,
    intended: object,
    address: object,
    halted: object = False,
    timed_out: object = False,
    lan_probe: object = "unknown",
) -> ListenDecision:
    """May this address be bound, classified, or observed?

    ``intended`` and ``address`` are required. Unknown names fail
    closed — UNKNOWN is not FALSE and is not admitted as loopback.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``bind`` only. Timeout forces status UNKNOWN and refuses bind;
    it does not classify the row as SUSPECTED and it does not prove
    loopback is absent.

    ``lan_probe`` must be a known probe name. A missing probe
    (``None``) is UNKNOWN, not closed and not a grant.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_addr = _require_name(address, what="address")
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    if lan_probe is None:
        raise FailClosedError(
            "lan_probe is UNKNOWN, not closed — refusing listen")
    probe_name = _require_member(
        lan_probe, what="lan_probe", allowed=PROBES)

    if _is_sealed(raw_intent) or _is_sealed(raw_addr):
        return ListenDecision(
            allowed=False,
            reason="sealed_effect",
            family="unknown",
            intended=raw_intent if raw_intent in INTENTS else "classify",
            address=raw_addr,
            status=classify_status(probe=probe_name, timed_out=timed_out),
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    family = classify_family(raw_addr)
    status = classify_status(probe=probe_name, timed_out=timed_out)

    if intent in {"classify", "observe"}:
        return ListenDecision(
            allowed=True,
            reason=None,
            family=family,
            intended=intent,
            address=raw_addr,
            status=status,
            timed_out=timed_out,
        )

    # bind — a START
    if halted:
        return ListenDecision(
            allowed=False,
            reason="halt_active",
            family=family,
            intended=intent,
            address=raw_addr,
            status=status,
            timed_out=timed_out,
        )

    if status == "UNKNOWN":
        return ListenDecision(
            allowed=False,
            reason="unknown_probe",
            family=family,
            intended=intent,
            address=raw_addr,
            status=status,
            timed_out=timed_out,
        )

    if family == "wildcard":
        return ListenDecision(
            allowed=False,
            reason="sealed_wildcard",
            family=family,
            intended=intent,
            address=raw_addr,
            status=status,
            timed_out=timed_out,
        )

    if family == "lan":
        return ListenDecision(
            allowed=False,
            reason="lan_not_local",
            family=family,
            intended=intent,
            address=raw_addr,
            status=status,
            timed_out=timed_out,
        )

    if family == "unknown":
        return ListenDecision(
            allowed=False,
            reason="unknown_address",
            family=family,
            intended=intent,
            address=raw_addr,
            status=status,
            timed_out=timed_out,
        )

    return ListenDecision(
        allowed=True,
        reason=None,
        family=family,
        intended=intent,
        address=raw_addr,
        status=status,
        timed_out=timed_out,
    )
