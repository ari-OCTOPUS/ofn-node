"""Append class — kernel-pure classifier for a store write mode.

The run store is append-only. This module is the second witness: is
this *mode* an append, a rewrite, or a truncate?

``append`` is the only admitted mode. ``rewrite`` and ``truncate``
are known refusals — they are not classified as FALSE and they are
not admitted. A missing or unknown mode is UNKNOWN, not rewrite.

A sealed send/ready name is never a kind and never a mode.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

HALT stops STARTS. This classifier has no halt parameter: an
in-flight append must still be classifiable so recovery does not
need the owner.

Not wired into the run store (that file is owned by another open
change).

Admitting an append is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import EVENT_KINDS, is_forbidden_effect_name

# Closed mode vocabulary. Widen only with a test.
MODES = frozenset({"append"})

# Known refused modes. These are a refusal, not an unknown.
REFUSED_MODES = frozenset({"rewrite", "truncate"})

# Known refusals. Unknown names fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({"rewrite", "truncate", "sealed_effect"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An append classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_append() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight appends."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Classification is not chattr +i."""
    return False


def unknown_mode_is_rewrite() -> bool:
    """Structurally False. A missing mode is UNKNOWN, not rewrite."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a mode is not an external effect."""
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


def classify_mode(mode: object) -> str:
    """Return the write mode, or fail closed.

    Unknown names are not classified as rewrite and are not FALSE.
    ``rewrite`` / ``truncate`` are known modes (then refused on
    admit), not an unknown.
    """
    name = _require_name(mode, what="mode")
    folded = name.strip().lower()
    if folded == "append":
        return "append"
    if folded in REFUSED_MODES:
        return folded
    raise FailClosedError(
        f"unknown write mode is not a refusal and not a grant: {mode!r}")


@dataclass(frozen=True)
class AppendDecision:
    """The append-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    mode: str
    kind: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "AppendDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — an append class is not a send")
        object.__setattr__(self, "mode", _require_name(self.mode, what="mode"))
        object.__setattr__(self, "kind", _require_name(self.kind, what="kind"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed append must not carry a reason: {self.reason!r}")
            if self.mode != "append":
                raise FailClosedError(
                    "AppendDecision cannot allow a rewrite or truncate")
            if _is_sealed(self.mode) or _is_sealed(self.kind):
                raise FailClosedError(
                    "AppendDecision cannot grant a sealed send/ready name")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
            if _is_sealed(self.mode) or _is_sealed(self.kind):
                if self.reason != "sealed_effect":
                    raise FailClosedError(
                        "AppendDecision cannot mis-label a sealed send/ready name")


def admit_append(
    *,
    mode: object,
    kind: object,
) -> AppendDecision:
    """May this write mode hit the store for this kind?

    ``mode`` and ``kind`` are required names. Unknown modes and
    unknown kinds fail closed — UNKNOWN is not FALSE and is not
    admitted. A sealed send/ready name is a known refusal
    (``sealed_effect``). ``rewrite`` and ``truncate`` are known
    refusals under their own reason.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    mode_name = _require_name(mode, what="mode")
    kind_name = _require_name(kind, what="kind")

    if _is_sealed(mode_name) or _is_sealed(kind_name):
        return AppendDecision(
            allowed=False,
            reason="sealed_effect",
            mode=mode_name,
            kind=kind_name,
        )

    classified = classify_mode(mode_name)
    if classified in REFUSED_MODES:
        return AppendDecision(
            allowed=False,
            reason=classified,
            mode=classified,
            kind=kind_name,
        )

    if kind_name not in EVENT_KINDS:
        raise FailClosedError(
            f"unknown event kind is not an append: {kind_name!r}")

    return AppendDecision(
        allowed=True,
        reason=None,
        mode="append",
        kind=kind_name,
    )
