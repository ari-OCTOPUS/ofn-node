"""Local pin — kernel-pure second witness for listen_class families.

``listen_class`` names a family and admits or refuses a bind.
This module is the pin: which families may ever be called local,
and which observations must not promote?

Closed pin vocabulary:

  local     → family is loopback
  foreign   → family is wildcard or lan
  unknown   → family is unknown

A wildcard is never local. A LAN address is never local.
A missing LAN probe never proves loopback is absent.
A timeout never proves absence and never proves a race.

A sealed send/ready name is never a family. ``campaign_envelope_ready``
is structurally distinct from ``send_authorized``; both are refused.

HALT stops STARTS. This pin has no halt parameter: an in-flight
family name must still be classifiable so recovery does not need
the owner.

Not wired into the run store or any adapter. Pinning a family is
not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .listen_class import FAMILIES

# Closed pin vocabulary. Widen only with a test.
PIN_VERDICTS = frozenset({"local", "foreign", "unknown"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A local pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not family pinning."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def wildcard_is_local() -> bool:
    """Structurally False. Wildcard stays foreign."""
    return False


def lan_is_local() -> bool:
    """Structurally False. LAN stays foreign."""
    return False


def unknown_family_is_local() -> bool:
    """Structurally False. Unknown is unknown, not local."""
    return False


def missing_lan_proves_absent() -> bool:
    """Structurally False. Missing LAN is inference, not absence."""
    return False


def timeout_proves_absent() -> bool:
    """Structurally False. Timeout is UNKNOWN, not 'API missing'."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a second writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Pinning a family is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {_fold(s) for s in _SEALED}


def _require_family(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"family must be a name: {value!r}")
    name = value.strip()
    if _is_sealed(name):
        raise FailClosedError(
            f"family names a sealed send/ready state: {name!r}")
    if name not in FAMILIES:
        raise FailClosedError(
            f"unknown family is not a pin and not a grant: {name!r}")
    return name


@dataclass(frozen=True)
class LocalPin:
    """One family pin. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``verdict`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    verdict: str
    family: str
    local: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "LocalPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pin is not a send")
        if self.verdict not in PIN_VERDICTS:
            raise FailClosedError(f"unknown pin verdict: {self.verdict!r}")
        if self.family not in FAMILIES:
            raise FailClosedError(f"unknown pin family: {self.family!r}")
        if type(self.local) is not bool:
            raise FailClosedError(
                f"local must be an exact bool: {self.local!r}")
        if _is_sealed(self.verdict) or _is_sealed(self.family):
            raise FailClosedError(
                "LocalPin cannot carry a sealed send/ready name")
        if self.verdict == "local":
            if self.family != "loopback" or self.local is not True:
                raise FailClosedError(
                    "local pin requires loopback and local=True")
        else:
            if self.local is True:
                raise FailClosedError(
                    "foreign/unknown pin cannot claim local=True")
        if self.verdict == "unknown" and self.family != "unknown":
            raise FailClosedError(
                "unknown pin requires unknown family")
        if self.verdict == "foreign" and self.family not in {"wildcard", "lan"}:
            raise FailClosedError(
                "foreign pin requires wildcard or lan")


def pin_family(*, family: object) -> LocalPin:
    """Pin one listen family as local, foreign, or unknown.

    ``family`` is required. A missing family (``None``) is UNKNOWN,
    not loopback. A sealed send/ready name fails closed.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    if family is None:
        raise FailClosedError(
            "family is UNKNOWN, not loopback — refusing pin")
    name = _require_family(family)
    if name == "loopback":
        verdict = "local"
        local = True
    elif name == "unknown":
        verdict = "unknown"
        local = False
    else:
        verdict = "foreign"
        local = False
    return LocalPin(
        verdict=verdict,
        family=name,
        local=local,
    )


def pin_allows_bind(pin: LocalPin) -> bool:
    """A bind is allowed only for a local pin. Foreign/unknown refuse.

    This is a second witness, not a second send path. The return is
    a bool about the pin, never a grant of ``send_authorized``.
    """
    if not isinstance(pin, LocalPin):
        raise FailClosedError(f"pin must be a LocalPin: {pin!r}")
    return pin.verdict == "local" and pin.local is True


def missing_probe_inference() -> Optional[str]:
    """Missing LAN is inference, not a verdict of absence.

    Returns None so a caller cannot treat the pin as a missing-body
    claim. The name of the claim is recorded here as the function
    identity; the value stays None.
    """
    return None
