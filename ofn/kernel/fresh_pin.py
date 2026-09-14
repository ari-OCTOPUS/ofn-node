"""Fresh-pin — pin a FRESH classification once.

``stale_class`` decides whether an age is FRESH / STALE / UNKNOWN.
This module is the second witness: may that FRESH verdict be
remembered for a named ``(run_id, event_id)``?

A first pin of a FRESH pair is admitted. A second pin of the
same pair is ``already_pinned``. STALE cannot be pinned as
FRESH. UNKNOWN stays unknown — it is not FALSE and it is not
a fresh pin. ``peek`` never writes.

A sealed send/ready name is never a run_id and never an event_id.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both fail closed.

Timeout is UNKNOWN. It does not prove a second writer and it
does not pin.

HALT stops STARTS. This pin has no halt parameter: in-flight
pin/peek must still work so recovery does not need the owner.

Not wired into the run store. Pinning FRESH is not
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set, Tuple

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .event_id import EVENT_ID_RE
from .events import is_forbidden_effect_name
from .stale_class import FRESH, KINDS, STALE, UNKNOWN, _fold, _is_sealed

INTENTS = frozenset({"pin", "peek"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "already_pinned",
    "stale_not_fresh",
    "unknown_not_fresh",
    "malformed_id",
})


def grants_send() -> bool:
    """A fresh pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_fresh() -> bool:
    """Structurally False. UNKNOWN cannot be pinned as FRESH."""
    return False


def stale_is_fresh() -> bool:
    """Structurally False. STALE cannot be pinned as FRESH."""
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
    """Structurally False. Complementary; not imported by the store."""
    return False


def persist_is_send() -> bool:
    """Structurally False. Remembering a pair is not a send."""
    return False


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_run_id(value: object) -> str:
    name = _require_name(value, what="run_id")
    if _is_sealed(name):
        raise FailClosedError(
            f"run_id names a sealed send/ready state: {name!r}")
    if RUN_ID_RE.match(name) is None:
        raise FailClosedError(f"run_id not minted at the boundary: {name!r}")
    return name


def _require_event_id(value: object) -> str:
    name = _require_name(value, what="event_id")
    if _is_sealed(name):
        raise FailClosedError(
            f"event_id names a sealed send/ready state: {name!r}")
    if EVENT_ID_RE.match(name) is None:
        raise FailClosedError(f"event_id not boundary-minted: {name!r}")
    return name


@dataclass(frozen=True)
class FreshPin:
    """Admission of a FRESH pin/peek. ``grants_send`` is False."""

    allowed: bool
    reason: Optional[str]
    intended: str
    kind: str
    run_id: str
    event_id: str
    seen: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "FreshPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pin is not a send")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if self.kind not in KINDS:
            raise FailClosedError(
                f"unknown stale kind is not a negative witness: {self.kind!r}")
        if type(self.seen) is not bool:
            raise FailClosedError(f"seen must be an exact bool: {self.seen!r}")
        object.__setattr__(self, "run_id", _require_name(self.run_id, what="run_id"))
        object.__setattr__(
            self, "event_id", _require_name(self.event_id, what="event_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed pin must not carry a reason: {self.reason!r}")
            if self.intended == "pin" and self.kind != FRESH:
                raise FailClosedError("only FRESH may be pinned")
            if self.intended == "pin" and self.seen:
                raise FailClosedError(
                    "FreshPin cannot allow a pin that is already seen")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.run_id) or _is_sealed(self.event_id):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "FreshPin cannot grant or mis-label a sealed "
                    "send/ready name")


class FreshIndex:
    """Append-only in-memory ``(run_id, event_id)`` set. Peek does not write."""

    def __init__(self) -> None:
        self._seen: Set[Tuple[str, str]] = set()
        self._order: list[Tuple[str, str]] = []

    def seen(self, run_id: str, event_id: str) -> bool:
        run_id = _require_run_id(run_id)
        event_id = _require_event_id(event_id)
        return (run_id, event_id) in self._seen

    def record(self, run_id: str, event_id: str) -> Tuple[str, str]:
        run_id = _require_run_id(run_id)
        event_id = _require_event_id(event_id)
        pair = (run_id, event_id)
        if pair in self._seen:
            raise FailClosedError(
                f"already_pinned: {run_id!r} {event_id!r}")
        self._seen.add(pair)
        self._order.append(pair)
        return pair

    def __len__(self) -> int:
        return len(self._order)


def pin_fresh(
    index: FreshIndex,
    *,
    intended: object,
    kind: object,
    run_id: object,
    event_id: object,
) -> FreshPin:
    """Pin or peek a classified age against an in-memory index.

    ``peek`` never writes. ``pin`` writes only on first FRESH success.
    STALE / UNKNOWN refuse. Sealed names refuse as ``sealed_effect``.
    Unknown format refuses as ``malformed_id`` — not FALSE.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    if not isinstance(index, FreshIndex):
        raise FailClosedError(f"index must be a FreshIndex: {type(index)!r}")
    raw_intent = _require_name(intended, what="intended")
    raw_kind = _require_name(kind, what="kind")
    raw_run = _require_name(run_id, what="run_id")
    raw_evt = _require_name(event_id, what="event_id")

    if (
        _is_sealed(raw_intent)
        or _is_sealed(raw_kind)
        or _is_sealed(raw_run)
        or _is_sealed(raw_evt)
    ):
        return FreshPin(
            allowed=False,
            reason="sealed_effect",
            intended=raw_intent if raw_intent in INTENTS else "peek",
            kind=UNKNOWN,
            run_id=raw_run,
            event_id=raw_evt,
            seen=False,
        )

    folded_intent = _fold(raw_intent)
    if folded_intent not in INTENTS:
        raise FailClosedError(
            f"unknown intended is not a refusal and not a grant: {raw_intent!r}")

    folded_kind = _fold(raw_kind)
    kind_map = {"fresh": FRESH, "stale": STALE, "unknown": UNKNOWN}
    if folded_kind not in kind_map:
        raise FailClosedError(
            f"unknown stale kind is not a negative witness: {kind!r}")
    resolved_kind = kind_map[folded_kind]

    if RUN_ID_RE.match(raw_run) is None or EVENT_ID_RE.match(raw_evt) is None:
        return FreshPin(
            allowed=False,
            reason="malformed_id",
            intended=folded_intent,
            kind=resolved_kind,
            run_id=raw_run,
            event_id=raw_evt,
            seen=False,
        )

    pair_seen = index.seen(raw_run, raw_evt)

    if folded_intent == "peek":
        return FreshPin(
            allowed=True,
            reason=None,
            intended="peek",
            kind=resolved_kind,
            run_id=raw_run,
            event_id=raw_evt,
            seen=pair_seen,
        )

    if resolved_kind == STALE:
        return FreshPin(
            allowed=False,
            reason="stale_not_fresh",
            intended="pin",
            kind=STALE,
            run_id=raw_run,
            event_id=raw_evt,
            seen=pair_seen,
        )
    if resolved_kind == UNKNOWN:
        return FreshPin(
            allowed=False,
            reason="unknown_not_fresh",
            intended="pin",
            kind=UNKNOWN,
            run_id=raw_run,
            event_id=raw_evt,
            seen=pair_seen,
        )
    if pair_seen:
        return FreshPin(
            allowed=False,
            reason="already_pinned",
            intended="pin",
            kind=FRESH,
            run_id=raw_run,
            event_id=raw_evt,
            seen=True,
        )

    index.record(raw_run, raw_evt)
    return FreshPin(
        allowed=True,
        reason=None,
        intended="pin",
        kind=FRESH,
        run_id=raw_run,
        event_id=raw_evt,
        seen=False,
    )
