"""Once pin — a classified nonce may be consumed at most once.

``nonce_class`` decides whether a token may be presented.
This module is the second witness: may that token be *burned*
for a named run?

A first consume of ``(nonce, run_id)`` is admitted. A second
consume of the same pair is ``already_consumed``. The same
nonce presented for a different run is ``nonce_collision``.
``peek`` never writes.

A sealed send/ready name is never a nonce and never a run_id.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both fail closed.

Timeout is UNKNOWN. It does not prove a second writer and it
does not consume.

HALT stops STARTS. This pin has no halt parameter: in-flight
consume/peek must still work so recovery does not need the
owner.

Not wired into the run store. Consuming a nonce is not
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
Ready is not authorized. A remembered pair is not a send.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set, Tuple

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .nonce_class import NONCE_RE, require_nonce

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"consume", "peek"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "already_consumed",
    "nonce_collision",
    "malformed_nonce",
    "malformed_id",
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
    """A once pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_consume() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight consume."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A consume pin is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a second writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Consuming a nonce is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A nonce burn is not an envelope-key burn."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove a second writer."""
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


def _require_run_id(value: object) -> str:
    name = _require_name(value, what="run_id")
    if _is_sealed(name):
        raise FailClosedError(
            f"run_id names a sealed send/ready state: {name!r}")
    if RUN_ID_RE.match(name) is None:
        raise FailClosedError(f"run_id not minted at the boundary: {name!r}")
    return name


@dataclass(frozen=True)
class OnceDecision:
    """The consume/peek verdict. ``grants_send`` is structurally False.

    ``allowed`` and ``grants_send`` are both recorded so a silent
    default cannot masquerade as an authorization.
    """

    allowed: bool
    reason: Optional[str]
    intended: str
    nonce: str
    run_id: str
    seen: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "OnceDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a once pin is not a send")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.seen) is not bool:
            raise FailClosedError(f"seen must be an exact bool: {self.seen!r}")
        object.__setattr__(self, "nonce", _require_name(self.nonce, what="nonce"))
        object.__setattr__(self, "run_id", _require_name(self.run_id, what="run_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed once must not carry a reason: {self.reason!r}")
            if self.intended == "consume" and self.seen:
                raise FailClosedError(
                    "OnceDecision cannot allow a consume that is already seen")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.nonce) or _is_sealed(self.run_id):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "OnceDecision cannot grant or mis-label a sealed "
                    "send/ready name")


class OnceIndex:
    """Append-only in-memory ``(nonce, run_id)`` set. Peek does not write."""

    def __init__(self) -> None:
        self._seen: Set[Tuple[str, str]] = set()
        self._by_nonce: dict[str, str] = {}
        self._order: list[Tuple[str, str]] = []

    def seen(self, nonce: str, run_id: str) -> bool:
        nonce = require_nonce(nonce)
        run_id = _require_run_id(run_id)
        return (nonce, run_id) in self._seen

    def owner(self, nonce: str) -> Optional[str]:
        nonce = require_nonce(nonce)
        return self._by_nonce.get(nonce)

    def record(self, nonce: str, run_id: str) -> Tuple[str, str]:
        nonce = require_nonce(nonce)
        run_id = _require_run_id(run_id)
        prior = self._by_nonce.get(nonce)
        if prior is not None and prior != run_id:
            raise FailClosedError(
                f"nonce_collision: {nonce!r} already bound to another run")
        pair = (nonce, run_id)
        if pair in self._seen:
            raise FailClosedError(
                f"already_consumed: {nonce!r} for {run_id!r}")
        self._seen.add(pair)
        self._by_nonce[nonce] = run_id
        self._order.append(pair)
        return pair

    def __len__(self) -> int:
        return len(self._order)


def pin_once(
    index: OnceIndex,
    *,
    intended: object,
    nonce: object,
    run_id: object,
) -> OnceDecision:
    """Consume or peek a classified nonce against an in-memory index.

    ``peek`` never writes. ``consume`` writes only on first success.
    Sealed names refuse as ``sealed_effect``. Unknown format refuses
    as ``malformed_nonce`` / ``malformed_id`` — not FALSE.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    if not isinstance(index, OnceIndex):
        raise FailClosedError(f"index must be an OnceIndex: {type(index)!r}")
    raw_intent = _require_name(intended, what="intended")
    raw_nonce = _require_name(nonce, what="nonce")
    raw_run = _require_name(run_id, what="run_id")

    if _is_sealed(raw_intent) or _is_sealed(raw_nonce) or _is_sealed(raw_run):
        return OnceDecision(
            allowed=False,
            reason="sealed_effect",
            intended=raw_intent if raw_intent in INTENTS else "peek",
            nonce=raw_nonce,
            run_id=raw_run,
            seen=False,
        )

    if raw_intent not in INTENTS:
        raise FailClosedError(
            f"unknown intended is not a refusal and not a grant: {raw_intent!r}")

    if NONCE_RE.match(raw_nonce) is None:
        return OnceDecision(
            allowed=False,
            reason="malformed_nonce",
            intended=raw_intent,
            nonce=raw_nonce,
            run_id=raw_run,
            seen=False,
        )
    if RUN_ID_RE.match(raw_run) is None:
        return OnceDecision(
            allowed=False,
            reason="malformed_id",
            intended=raw_intent,
            nonce=raw_nonce,
            run_id=raw_run,
            seen=False,
        )

    prior = index.owner(raw_nonce)
    pair_seen = index.seen(raw_nonce, raw_run)

    if raw_intent == "peek":
        return OnceDecision(
            allowed=True,
            reason=None,
            intended="peek",
            nonce=raw_nonce,
            run_id=raw_run,
            seen=pair_seen,
        )

    if prior is not None and prior != raw_run:
        return OnceDecision(
            allowed=False,
            reason="nonce_collision",
            intended="consume",
            nonce=raw_nonce,
            run_id=raw_run,
            seen=False,
        )
    if pair_seen:
        return OnceDecision(
            allowed=False,
            reason="already_consumed",
            intended="consume",
            nonce=raw_nonce,
            run_id=raw_run,
            seen=True,
        )

    index.record(raw_nonce, raw_run)
    return OnceDecision(
        allowed=True,
        reason=None,
        intended="consume",
        nonce=raw_nonce,
        run_id=raw_run,
        seen=False,
    )
