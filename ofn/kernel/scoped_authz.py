"""Pin an authorization as explicit, newer, and scoped.

quote_sent and other external effects stay forbidden until a
caller-supplied record is all three: present (explicit),
authz_epoch > hold_epoch (newer), and a non-wildcard scope.
This pin classifies that record. It never grants a send.

Missing authz or hold or scope is UNKNOWN (None), not FALSE
and not a stale-or-unscoped guess. Same-epoch is a shape
error, not newer. Wildcard / sealed send-ready names fail
closed. campaign_envelope_ready is not scoped authorization.

Distinct from later_hold (epoch class), send_fence (name
promotion), campaign_bind (ready class), phase_wall /
flag_freeze (bool later_hold parameter), and hold_class /
disarm_pin (other open change). Not wired into run_store.py.
HALT stops STARTS, not this pin.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name, require_epoch_s
from .errors import FailClosedError
from .events import is_forbidden_effect_name

AUTHZ_SCOPED = "AUTHZ_SCOPED"
AUTHZ_STALE = "AUTHZ_STALE"
UNKNOWN = "UNKNOWN"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})
_WILDCARD = frozenset({
    "*",
    "all",
    "any",
    "wildcard",
    "0.0.0.0",
    "::",
    "::/0",
})


def grants_send() -> bool:
    """A scoped-authz pin never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. Classification does not re-arm outbound."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A pin is not a rename of authorized."""
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


def wires_into_run_store() -> bool:
    """Structurally False. This module is not imported by the store."""
    return False


def scoped_is_send() -> bool:
    """Structurally False. AUTHZ_SCOPED is a class, not a send grant."""
    return False


def later_hold_supersedes_older() -> bool:
    """Structurally True. Stale authz after a later hold is not scoped."""
    return True


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed_name(value: object, *, what: str) -> None:
    if type(value) is not str:
        return
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {s.replace("-", "_") for s in _SEALED}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "ready is not scoped authorization")


def _epoch_or_unknown(value: object, *, what: str) -> Optional[int]:
    if value is None:
        return None
    _refuse_sealed_name(value, what=what)
    return require_epoch_s(value, what)


def _scope_or_unknown(value: object) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"scope must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError("scope is empty")
    _refuse_sealed_name(value, what="scope")
    folded = _fold(value)
    if value.strip() in _WILDCARD or folded in _WILDCARD:
        raise FailClosedError(
            f"scope is wildcard: {value!r} — scoped is not all")
    if not _SCOPE_OK(folded):
        raise FailClosedError(f"scope is not a scoped token: {value!r}")
    return folded


def _SCOPE_OK(folded: str) -> bool:
    if not folded or folded[0] < "a" or folded[0] > "z":
        return False
    for ch in folded:
        ok = ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch == "_"
        if not ok:
            return False
    return len(folded) <= 64


def classify_authz(
    authz_epoch: object, hold_epoch: object, scope: object,
) -> str:
    """AUTHZ_SCOPED, AUTHZ_STALE, or UNKNOWN.

    Missing any side is UNKNOWN, not FALSE. Equal epochs fail
    closed — same instant is not newer. Wildcard / sealed /
    empty / bool fail closed (shape error), not UNKNOWN.
    """
    authz = _epoch_or_unknown(authz_epoch, what="authz_epoch")
    hold = _epoch_or_unknown(hold_epoch, what="hold_epoch")
    named = _scope_or_unknown(scope)
    if authz is None or hold is None or named is None:
        return UNKNOWN
    if authz == hold:
        raise FailClosedError(
            "authz_epoch equals hold_epoch — same epoch is not newer")
    if authz < hold:
        return AUTHZ_STALE
    return AUTHZ_SCOPED


def pin_allows_effect(klass: object) -> bool:
    """True is unreachable. SCOPED is still not a send.

    UNKNOWN / STALE / missing return False only when the class is
    a known non-grant. Unknown class names fail closed.
    """
    if klass is None:
        return False
    if type(klass) is not str:
        raise FailClosedError(f"klass must be a str or None: {klass!r}")
    folded = _fold(klass)
    if folded in {AUTHZ_SCOPED.lower(), AUTHZ_STALE.lower(), UNKNOWN.lower()}:
        return False
    _refuse_sealed_name(klass, what="klass")
    raise FailClosedError(f"unknown authz class: {klass!r}")


@dataclass(frozen=True)
class ScopedAuthz:
    """One explicit newer scoped record. Frozen so a later write
    cannot silently retcon it into send_authorized.
    """

    authz_epoch: int
    hold_epoch: int
    scope: str
    authz_class: str


def pin_scoped(
    authz_epoch: object, hold_epoch: object, scope: object,
) -> ScopedAuthz:
    """Require AUTHZ_SCOPED. Missing fails closed (use try_pin)."""
    klass = classify_authz(authz_epoch, hold_epoch, scope)
    if klass == UNKNOWN:
        raise FailClosedError(
            "authz missing — UNKNOWN is not a scoped pin")
    if klass != AUTHZ_SCOPED:
        raise FailClosedError(
            f"authz is {klass}, not AUTHZ_SCOPED — stale is not newer")
    return ScopedAuthz(
        authz_epoch=require_epoch_s(authz_epoch, "authz_epoch"),
        hold_epoch=require_epoch_s(hold_epoch, "hold_epoch"),
        scope=_scope_or_unknown(scope) or "",
        authz_class=AUTHZ_SCOPED,
    )


def try_pin(
    authz_epoch: object, hold_epoch: object, scope: object,
) -> Optional[ScopedAuthz]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    if authz_epoch is None or hold_epoch is None or scope is None:
        return None
    return pin_scoped(authz_epoch, hold_epoch, scope)
