"""Stale-class — classify a caller-supplied age as FRESH, STALE, or UNKNOWN.

The kernel reads no clock. ``observed_epoch_s``, ``as_of_epoch_s``,
and ``ttl_s`` arrive as exact ints. Missing either epoch is UNKNOWN,
not STALE and not FALSE. A timeout/error witness is UNKNOWN — it
does not prove a concurrent writer and it is not a stale verdict.

Equal age == ttl is still FRESH (the window is open on the
boundary). Strictly greater is STALE. ``as_of`` before
``observed`` fail-closes — inversion is not STALE.

Distinct from ``deadline_window`` (open/closed create window),
``timeout_verdict`` (elapsed vs budget), ``clock_bind`` /
``utc_class`` (stamp class), and ``phase_wall``.

A sealed send/ready name is never an epoch and never an intent.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both fail closed.

``classify`` / ``observe`` continue under HALT (not a START).
``admit_refresh`` is a START and is refused when halted.

Not wired into the run store.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .halt import is_halted

FRESH = "FRESH"
STALE = "STALE"
UNKNOWN = "UNKNOWN"

KINDS = frozenset({FRESH, STALE, UNKNOWN})

# Closed intent vocabulary. Widen only with a test.
CLASSIFY_INTENTS = frozenset({"classify", "observe"})
REFRESH_INTENTS = frozenset({"refresh"})

REFUSAL_REASONS = frozenset({
    "halt_blocks_start",
    "already_fresh",
    "unknown_age",
    "sealed_effect",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A stale class never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_refresh() -> bool:
    """Structurally True. Refresh is a START."""
    return True


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_stale() -> bool:
    """Structurally False. Missing/timeout is UNKNOWN, not STALE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A classify is not a rename of authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Proposal is not execution."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Not wired into the run store."""
    return False


def equal_age_is_stale() -> bool:
    """Structurally False. age == ttl stays FRESH (window still open)."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {_fold(s) for s in _SEALED}


def _refuse_sealed(value: object, *, what: str) -> None:
    if isinstance(value, str):
        if _is_sealed(value) or _is_sealed(_fold(value)):
            raise FailClosedError(
                f"{what} names a sealed send/ready state: {value!r} — "
                "ready is not authorized")


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_epoch(value: object, *, what: str) -> int:
    _refuse_sealed(value, what=what)
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"{what} must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{what} must be non-negative: {value!r}")
    return value


def _require_optional_epoch(value: object, *, what: str) -> Optional[int]:
    if value is None:
        return None
    return _require_epoch(value, what=what)


def _require_ttl(value: object) -> int:
    _refuse_sealed(value, what="ttl_s")
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"ttl_s must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(f"ttl_s must be non-negative: {value!r}")
    return value


@dataclass(frozen=True)
class StaleClass:
    """A classified age. ``grants_send`` is structurally False."""

    kind: str
    observed_epoch_s: Optional[int]
    as_of_epoch_s: Optional[int]
    ttl_s: int
    age_s: Optional[int]
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "StaleClass cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a classify is not a send")
        if self.kind not in KINDS:
            raise FailClosedError(
                f"unknown stale kind is not a negative witness: {self.kind!r}")
        if type(self.ttl_s) is not int or isinstance(self.ttl_s, bool):
            raise FailClosedError(f"ttl_s must be an exact int: {self.ttl_s!r}")
        if self.ttl_s < 0:
            raise FailClosedError(f"ttl_s must be non-negative: {self.ttl_s!r}")
        if self.kind == UNKNOWN:
            if self.age_s is not None:
                raise FailClosedError(
                    "UNKNOWN age must not carry a computed age_s")
        else:
            if self.observed_epoch_s is None or self.as_of_epoch_s is None:
                raise FailClosedError(
                    "FRESH/STALE must record both epochs")
            if self.age_s is None:
                raise FailClosedError("FRESH/STALE must record age_s")
            if self.age_s != self.as_of_epoch_s - self.observed_epoch_s:
                raise FailClosedError("age_s must equal as_of - observed")
            if self.kind == FRESH and self.age_s > self.ttl_s:
                raise FailClosedError("FRESH cannot have age_s > ttl_s")
            if self.kind == STALE and self.age_s <= self.ttl_s:
                raise FailClosedError("STALE cannot have age_s <= ttl_s")


@dataclass(frozen=True)
class RefreshDecision:
    """Admission of a refresh START. ``grants_send`` is False."""

    allowed: bool
    reason: Optional[str]
    kind: str
    halted: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "RefreshDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a refresh is not a send")
        if self.kind not in KINDS:
            raise FailClosedError(
                f"unknown stale kind is not a negative witness: {self.kind!r}")
        if type(self.halted) is not bool:
            raise FailClosedError(f"halted must be an exact bool: {self.halted!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed refresh must not carry a reason: {self.reason!r}")
            if self.kind != STALE:
                raise FailClosedError("only STALE may be refreshed")
            if self.halted:
                raise FailClosedError("RefreshDecision cannot allow under HALT")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")


def classify_age(
    *,
    observed_epoch_s: object = None,
    as_of_epoch_s: object = None,
    ttl_s: object,
    error: object = None,
    intent: object = "classify",
) -> StaleClass:
    """Classify observed vs as-of against ttl. Timeout/error forces UNKNOWN.

    ``intent`` is classify or observe. Both continue under HALT
    (this function has no halt parameter). Sealed names fail closed.
    Missing epoch is UNKNOWN, not STALE.
    """
    intent_name = _require_name(intent, what="intent")
    _refuse_sealed(intent_name, what="intent")
    folded_intent = _fold(intent_name)
    if folded_intent not in CLASSIFY_INTENTS:
        raise FailClosedError(
            f"unknown intent is not a refusal class and not a grant: "
            f"{intent!r}")

    ttl = _require_ttl(ttl_s)

    if error is not None:
        return StaleClass(
            kind=UNKNOWN,
            observed_epoch_s=None,
            as_of_epoch_s=None,
            ttl_s=ttl,
            age_s=None,
            grants_send=False,
        )

    observed = _require_optional_epoch(observed_epoch_s, what="observed_epoch_s")
    as_of = _require_optional_epoch(as_of_epoch_s, what="as_of_epoch_s")
    if observed is None or as_of is None:
        return StaleClass(
            kind=UNKNOWN,
            observed_epoch_s=observed,
            as_of_epoch_s=as_of,
            ttl_s=ttl,
            age_s=None,
            grants_send=False,
        )

    if as_of < observed:
        raise FailClosedError(
            f"as_of_epoch_s {as_of!r} before observed_epoch_s {observed!r} "
            "is inversion, not STALE")

    age = as_of - observed
    kind = FRESH if age <= ttl else STALE
    return StaleClass(
        kind=kind,
        observed_epoch_s=observed,
        as_of_epoch_s=as_of,
        ttl_s=ttl,
        age_s=age,
        grants_send=False,
    )


def admit_refresh(
    *,
    classified: object,
    halt: object,
) -> RefreshDecision:
    """Admit a refresh START from a classified age.

    HALT refuses. FRESH is ``already_fresh``. UNKNOWN is
    ``unknown_age`` — not FALSE and not admitted. Only STALE
    plus a non-halted switch is allowed.

    Signature is sealed: no send, no resend, no immutable.
    """
    if not isinstance(classified, StaleClass):
        raise FailClosedError(
            f"classified must be a StaleClass: {type(classified)!r}")
    if isinstance(halt, bool):
        raw = "1" if halt else "0"
    elif halt is None or isinstance(halt, str):
        raw = halt
    else:
        raise FailClosedError(f"halt must be bool or raw flag: {halt!r}")
    halted = is_halted(raw)

    if classified.kind == UNKNOWN:
        return RefreshDecision(
            allowed=False,
            reason="unknown_age",
            kind=UNKNOWN,
            halted=halted,
            grants_send=False,
        )
    if halted:
        return RefreshDecision(
            allowed=False,
            reason="halt_blocks_start",
            kind=classified.kind,
            halted=True,
            grants_send=False,
        )
    if classified.kind == FRESH:
        return RefreshDecision(
            allowed=False,
            reason="already_fresh",
            kind=FRESH,
            halted=False,
            grants_send=False,
        )
    return RefreshDecision(
        allowed=True,
        reason=None,
        kind=STALE,
        halted=False,
        grants_send=False,
    )
