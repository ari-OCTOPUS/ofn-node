"""Numeric claim — a number is not a fact without a receipt.

Every numeric claim carries: command, utc_iso, head_sha (full 40 hex),
exit_code, receipt_path, and an exact int value. A number without a
source is refused. Small n is UNDERPOWERED, never "improved".

This module does not run the command. The caller supplies every field.
The kernel only classifies.

Not wired into the run store (that file is owned by an open change).

Recording a number is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: dataclasses + re + typing. No json, no clock, no I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .artifact_ref import require_rel_path
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed power vocabulary. Widen only with a test. "improved" is not
# a label this module can emit.
POWER_LABELS = frozenset({"UNDERPOWERED", "AT_THRESHOLD"})

UTC_Z_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
)
HEAD_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A numeric claim never authorizes a send. Structurally False."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A number is not chattr +i."""
    return False


def claims_improved() -> bool:
    """Structurally False. This module cannot emit 'improved'."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def halt_blocks_claim() -> bool:
    """Structurally False. HALT stops STARTS, not numeric citation."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _refuse_sealed(value: str, *, what: str) -> None:
    if _is_sealed(value):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    for part in value.replace("\\", "/").split("/"):
        if _is_sealed(part):
            raise FailClosedError(
                f"{what} path component names a sealed send/ready "
                f"state: {part!r}")


def require_exact_int(value: object, *, what: str) -> int:
    """Exact int. ``True`` / ``1.0`` / ``\"1\"`` are not integers."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"{what} must be exact int: {value!r}")
    return value


def require_command(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"command must be a non-empty string: {value!r}")
    text = value.strip()
    _refuse_sealed(text, what="command")
    return text


def require_utc_z(value: object, *, what: str = "utc_iso") -> str:
    """Timezone-aware UTC ending in Z. Naive stamps fail closed."""
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a UTC Z stamp: {value!r}")
    text = value.strip()
    _refuse_sealed(text, what=what)
    if not UTC_Z_RE.match(text):
        raise FailClosedError(
            f"{what} must be YYYY-MM-DDTHH:MM:SSZ (UTC, Z suffix): {value!r}")
    return text


def require_head_sha(value: object) -> str:
    """Full 40-char lowercase hex. Short prefixes fail closed."""
    if isinstance(value, bool) or not isinstance(value, str):
        raise FailClosedError(f"head_sha must be a full 40-char hex: {value!r}")
    text = value.strip().lower()
    _refuse_sealed(text, what="head_sha")
    if not HEAD_SHA_RE.match(text):
        raise FailClosedError(
            f"head_sha must be a full 40-char git SHA: {value!r}")
    return text


def classify_sample_power(n: object, *, threshold: object) -> str:
    """Label a sample size against a caller-supplied threshold.

    The threshold is an argument, not a constant this module invented.
    ``n < threshold`` → UNDERPOWERED. ``n >= threshold`` → AT_THRESHOLD.
    This function never returns "improved".
    """
    size = require_exact_int(n, what="n")
    bar = require_exact_int(threshold, what="threshold")
    if bar <= 0:
        raise FailClosedError(f"threshold must be a positive int: {threshold!r}")
    if size < 0:
        raise FailClosedError(f"n must be non-negative: {n!r}")
    if size < bar:
        return "UNDERPOWERED"
    return "AT_THRESHOLD"


@dataclass(frozen=True)
class NumericClaim:
    """One measured integer. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``value`` and ``grants_send``
    are both recorded, and the constructor refuses ``grants_send=True``.
    """

    value: int
    command: str
    utc_iso: str
    head_sha: str
    exit_code: int
    receipt_path: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "NumericClaim cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a number is not a send")
        object.__setattr__(self, "value", require_exact_int(self.value, what="value"))
        object.__setattr__(self, "command", require_command(self.command))
        object.__setattr__(self, "utc_iso", require_utc_z(self.utc_iso))
        object.__setattr__(self, "head_sha", require_head_sha(self.head_sha))
        object.__setattr__(
            self, "exit_code", require_exact_int(self.exit_code, what="exit_code"))
        object.__setattr__(
            self, "receipt_path", require_rel_path(self.receipt_path, what="receipt_path"))


def mint_numeric_claim(
    *,
    value: object,
    command: object,
    utc_iso: object,
    head_sha: object,
    exit_code: object,
    receipt_path: object,
) -> NumericClaim:
    """The boundary's only sanctioned constructor.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``improved``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    return NumericClaim(
        value=require_exact_int(value, what="value"),
        command=require_command(command),
        utc_iso=require_utc_z(utc_iso),
        head_sha=require_head_sha(head_sha),
        exit_code=require_exact_int(exit_code, what="exit_code"),
        receipt_path=require_rel_path(receipt_path, what="receipt_path"),
        grants_send=False,
    )
