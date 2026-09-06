"""Write fence — kernel-pure admission for a durable write.

Start permit decides mint. Close gate decides append-after-close.
This module is the third witness: may this *record* hit a named
durable surface?

Surfaces are a closed vocabulary:

  ledger   — spine events (EVENT_KINDS except RUN_REJECTED)
  receipt  — EXECUTION_RECEIPT only
  side_log — RUN_REJECTED only (refusal witness, not a run)

A sealed send/ready name is never a surface, never a kind, never a
payload key or string value. ``campaign_envelope_ready`` is
structurally distinct from ``send_authorized``; both are refused.

HALT stops STARTS. This fence has no halt parameter: in-flight writes
must still be admitted so recovery does not need the owner.

Not wired into the run store (that file is owned by an open change).

Admitting a write is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .errors import FailClosedError
from .events import (
    EVENT_KINDS,
    EXECUTION_RECEIPT,
    RUN_REJECTED,
    is_forbidden_effect_name,
    payload_forbidden_effect,
)

# Closed surface vocabulary. Widen only with a test.
SURFACES = frozenset({"ledger", "receipt", "side_log"})

# Known refusals. Unknown kinds/surfaces fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({"sealed_effect", "surface_mismatch", "smuggled_effect"})

LEDGER_KINDS = frozenset(k for k in EVENT_KINDS if k != RUN_REJECTED)
RECEIPT_KINDS = frozenset({EXECUTION_RECEIPT})
SIDE_LOG_KINDS = frozenset({RUN_REJECTED})

_SURFACE_KINDS = {
    "ledger": LEDGER_KINDS,
    "receipt": RECEIPT_KINDS,
    "side_log": SIDE_LOG_KINDS,
}

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A write fence never authorizes a send. Structurally False."""
    return False


def halt_blocks_write() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight writes."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Admission is not chattr +i."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A refused write does not burn the key."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


@dataclass(frozen=True)
class WriteDecision:
    """The write-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    surface: str
    kind: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "WriteDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a write fence is not a send")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed write must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        object.__setattr__(self, "surface", _require_name(self.surface, what="surface"))
        object.__setattr__(self, "kind", _require_name(self.kind, what="kind"))
        # A sealed name may appear only as the subject of a sealed_effect
        # refusal. An allowed write, or any other refusal, cannot carry it.
        if _is_sealed(self.surface) or _is_sealed(self.kind):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "WriteDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_write(
    *,
    surface: object,
    kind: object,
    payload: Optional[Mapping[str, object]] = None,
) -> WriteDecision:
    """May this record hit this durable surface?

    ``surface`` and ``kind`` are required names. Unknown surfaces and
    unknown kinds fail closed — UNKNOWN is not FALSE and is not
    admitted. A sealed send/ready name is a known refusal
    (``sealed_effect``), not an unknown.

    ``payload`` is optional. When supplied it must be a mapping.
    A smuggled sealed name is a known refusal (``smuggled_effect``).

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    surface_name = _require_name(surface, what="surface")
    kind_name = _require_name(kind, what="kind")

    if _is_sealed(surface_name) or _is_sealed(kind_name):
        # Surface still has to be a known surface for the record to
        # name where the refusal happened. A sealed surface name is
        # itself a sealed_effect — we do not invent a ledger home.
        recorded_surface = surface_name if surface_name in SURFACES else surface_name
        return WriteDecision(
            allowed=False,
            reason="sealed_effect",
            surface=recorded_surface,
            kind=kind_name,
        )

    if surface_name not in SURFACES:
        raise FailClosedError(
            f"unknown write surface is not a refusal and not a grant: "
            f"{surface_name!r}")

    if kind_name not in EVENT_KINDS:
        raise FailClosedError(
            f"unknown event kind is not a write: {kind_name!r}")

    if payload is not None:
        if isinstance(payload, (str, bytes, bytearray)) or not isinstance(payload, Mapping):
            raise FailClosedError(f"payload must be a mapping: {payload!r}")
        smuggled = payload_forbidden_effect(payload)
        if smuggled is not None:
            return WriteDecision(
                allowed=False,
                reason="smuggled_effect",
                surface=surface_name,
                kind=kind_name,
            )

    allowed_kinds = _SURFACE_KINDS[surface_name]
    if kind_name not in allowed_kinds:
        return WriteDecision(
            allowed=False,
            reason="surface_mismatch",
            surface=surface_name,
            kind=kind_name,
        )

    return WriteDecision(
        allowed=True,
        reason=None,
        surface=surface_name,
        kind=kind_name,
    )
