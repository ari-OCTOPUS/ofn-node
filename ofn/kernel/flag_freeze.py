"""Flag freeze — kernel-pure admission for a named runtime flag.

A later hold outranks an older authorization. Opening a frozen
family is refused. Closing / disarming a frozen family is admitted
(reversible engineering). Unknown flag names fail closed — UNKNOWN
is not FALSE and is not an unfreeze.

Frozen families (closed vocabulary; widen only with a test):

  wire            — folded name contains ``_wire_`` or starts ``wire_``
  observatory     — folded name ``observatory``
  hypothesis      — folded name ``cortex_hypothesis``
  auto_email      — folded name ``auto_email``
  keep_gates_open — folded name ``keep_gates_open`` or
                    ``ofn_keep_gates_open``

A sealed send/ready name is never a flag. ``campaign_envelope_ready``
is structurally distinct from ``send_authorized``; both are refused
as ``sealed_effect``.

Admitting a close is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: a freeze
decision is not a run start.

Not wired into the run store (that file is owned by an open change).

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed family vocabulary. Widen only with a test.
FAMILIES = frozenset({
    "wire",
    "observatory",
    "hypothesis",
    "auto_email",
    "keep_gates_open",
})

# Closed intent vocabulary. "1" / True / "true" are UNKNOWN, not open.
INTENTS = frozenset({"closed", "open"})

# Known refusals. Unknown names fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({"frozen_open", "later_hold", "sealed_effect"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})

_KEEP_GATES = frozenset({"keep_gates_open", "ofn_keep_gates_open"})


def grants_send() -> bool:
    """A flag freeze never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A freeze cannot re-arm a later hold."""
    return False


def halt_blocks_flag() -> bool:
    """Structurally False. HALT stops STARTS, not flag classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Admission is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Admitting a close is not an external effect."""
    return False


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {s.replace("-", "_") for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def classify_family(name: object) -> str:
    """Return the frozen family for a flag name, or fail closed.

    Unknown names are not classified as unfrozen and are not FALSE.
    """
    flag = _require_name(name, what="flag")
    if _is_sealed(flag):
        raise FailClosedError(
            f"sealed send/ready name is not a flag: {flag!r}")
    folded = _fold(flag)
    if "_wire_" in folded or folded.startswith("wire_"):
        return "wire"
    if folded == "observatory":
        return "observatory"
    if folded == "cortex_hypothesis":
        return "hypothesis"
    if folded == "auto_email":
        return "auto_email"
    if folded in _KEEP_GATES:
        return "keep_gates_open"
    raise FailClosedError(
        f"unknown flag name is not a refusal and not a grant: {flag!r}")


@dataclass(frozen=True)
class FlagDecision:
    """The flag-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    family: str
    name: str
    intended: str
    later_hold: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "FlagDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a flag freeze is not a send")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.later_hold) is not bool:
            raise FailClosedError(
                f"later_hold must be an exact bool: {self.later_hold!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed flag must not carry a reason: {self.reason!r}")
            if self.intended != "closed":
                raise FailClosedError(
                    "FlagDecision cannot allow an open intent")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        object.__setattr__(self, "name", _require_name(self.name, what="flag"))
        object.__setattr__(self, "family", _require_name(self.family, what="family"))
        if self.family not in FAMILIES and self.reason != "sealed_effect":
            raise FailClosedError(
                f"unknown family is not a grant: {self.family!r}")
        if _is_sealed(self.name) or _is_sealed(self.family):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "FlagDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_flag(
    *,
    name: object,
    intended: object,
    later_hold: object = False,
) -> FlagDecision:
    """May this flag be set to this intended state?

    ``name`` and ``intended`` are required names. Unknown flags and
    unknown intents fail closed — UNKNOWN is not FALSE and is not
    admitted. A sealed send/ready name is a known refusal
    (``sealed_effect``), not an unknown.

    ``later_hold`` must be an exact bool. True means a later
    disarm/hold is on the record and outranks any older
    authorization: an open intent is refused as ``later_hold``.
    A close intent is still admitted.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    flag = _require_name(name, what="flag")

    if isinstance(later_hold, bool):
        hold = later_hold
    else:
        raise FailClosedError(
            f"later_hold must be an exact bool: {later_hold!r}")

    if isinstance(intended, bool) or not isinstance(intended, str):
        raise FailClosedError(
            f"intended must be a closed/open name: {intended!r}")
    intent = intended.strip()
    if intent not in INTENTS:
        raise FailClosedError(
            f"unknown intended is not a refusal and not a grant: {intended!r}")

    if _is_sealed(flag):
        return FlagDecision(
            allowed=False,
            reason="sealed_effect",
            family="sealed",
            name=flag,
            intended=intent,
            later_hold=hold,
        )

    family = classify_family(flag)

    if intent == "open" and hold:
        return FlagDecision(
            allowed=False,
            reason="later_hold",
            family=family,
            name=flag,
            intended=intent,
            later_hold=hold,
        )

    if intent == "open":
        return FlagDecision(
            allowed=False,
            reason="frozen_open",
            family=family,
            name=flag,
            intended=intent,
            later_hold=hold,
        )

    return FlagDecision(
        allowed=True,
        reason=None,
        family=family,
        name=flag,
        intended=intent,
        later_hold=hold,
    )
