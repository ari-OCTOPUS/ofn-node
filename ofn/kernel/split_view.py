"""Split view — two independent sources disagree; do not silently pick.

When two measurements of the same claim disagree, this module records
both values and leaves status open. An agent cannot close a row
(self-elevation ban). Resolution is reserved for the owner and is
not implemented here.

UNKNOWN is not FALSE. A missing side is UNKNOWN, not a pick of the
other side. Timeout does not prove concurrent write.

A split-view row is not send_authorized, quote_sent, or
campaign_envelope_ready. Ready is not authorized.

Not wired into the run store (that file is owned by an open change).

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError

# Closed status vocabulary. Widen only with a test.
STATUSES = frozenset({"match", "open", "unknown"})

# Sealed send/ready names. A claim or value that is one of these is
# refused. campaign_envelope_ready is listed so ready stays distinct
# from authorized: mentioning it is a defect, not a grant.
_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A split-view row never authorizes a send. Structurally False."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Recording a split is not executing a send."""
    return False


def agent_reported_is_verified() -> bool:
    """Structurally False. Agent-reported is not independently verified."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race proof."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A row is not chattr +i."""
    return False


def halt_blocks_row() -> bool:
    """Structurally False. HALT stops STARTS, not classification."""
    return False


def silently_picks() -> bool:
    """Structurally False. This module never picks a side."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_value(value: object, *, what: str) -> object:
    """Values are str or non-bool int. None means UNKNOWN. Float fails closed."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise FailClosedError(
            f"{what} bool is not a measured value: {value!r}")
    if isinstance(value, float):
        raise FailClosedError(
            f"{what} float is not an exact value: {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if not value.strip():
            raise FailClosedError(f"{what} empty string is not a value")
        if _is_sealed(value):
            raise FailClosedError(
                f"{what} cannot be a sealed send/ready name")
        return value
    raise FailClosedError(f"{what} must be str, int, or None: {value!r}")


def classify(value_a: object, value_b: object) -> str:
    """Name the relation. Missing either side is UNKNOWN, not a pick.

    Equal present values are MATCH — absence of difference is
    agreement, not inattention. Unequal present values are OPEN.
    """
    a = _require_value(value_a, what="value_a")
    b = _require_value(value_b, what="value_b")
    if a is None or b is None:
        return "unknown"
    if a == b:
        return "match"
    return "open"


@dataclass(frozen=True)
class SplitRow:
    """Both sides recorded. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``status`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    claim: str
    value_a: object
    source_a: str
    value_b: object
    source_b: str
    status: str
    resolution: Optional[str]
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "SplitRow cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a split view is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(f"unknown status: {self.status!r}")
        if self.resolution is not None:
            raise FailClosedError(
                "this module cannot carry a resolution — owner only")
        object.__setattr__(self, "claim", _require_name(self.claim, what="claim"))
        object.__setattr__(self, "source_a", _require_name(self.source_a, what="source_a"))
        object.__setattr__(self, "source_b", _require_name(self.source_b, what="source_b"))
        if self.source_a == self.source_b:
            raise FailClosedError(
                "sources must be independent — same source both sides")
        if _is_sealed(self.claim):
            raise FailClosedError(
                "claim cannot be a sealed send/ready name")
        object.__setattr__(
            self, "value_a", _require_value(self.value_a, what="value_a"))
        object.__setattr__(
            self, "value_b", _require_value(self.value_b, what="value_b"))
        expected = classify(self.value_a, self.value_b)
        if self.status != expected:
            raise FailClosedError(
                f"status {self.status!r} does not match classify "
                f"({expected!r}) — do not silently pick")


def mint_row(
    *,
    claim: object,
    value_a: object,
    source_a: object,
    value_b: object,
    source_b: object,
) -> SplitRow:
    """Record both sides of one claim.

    ``claim``, ``source_a``, and ``source_b`` are required names.
    Sources must be distinct. A sealed send/ready name as claim or
    value fails closed.

    ``value_a`` / ``value_b`` are str, non-bool int, or None.
    None is UNKNOWN, not zero and not a pick of the other side.
    Float fails closed — unknown precision is not an exact value.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``, no ``resolution``. Tests lock the parameter list; the
    kernel does not import inspect.
    """
    claim_name = _require_name(claim, what="claim")
    if _is_sealed(claim_name):
        raise FailClosedError("claim cannot be a sealed send/ready name")
    src_a = _require_name(source_a, what="source_a")
    src_b = _require_name(source_b, what="source_b")
    if src_a == src_b:
        raise FailClosedError(
            "sources must be independent — same source both sides")
    va = _require_value(value_a, what="value_a")
    vb = _require_value(value_b, what="value_b")
    status = classify(va, vb)
    return SplitRow(
        claim=claim_name,
        value_a=va,
        source_a=src_a,
        value_b=vb,
        source_b=src_b,
        status=status,
        resolution=None,
        grants_send=False,
    )


def resolve(row: SplitRow, resolution: object) -> None:
    """Refused. This module cannot close a split (self-elevation ban)."""
    raise FailClosedError(
        "this module cannot resolve a split — owner only; "
        f"row={row.claim!r} resolution={resolution!r}")


def pick_a(row: SplitRow) -> None:
    """Refused. Silently picking value_a is forbidden."""
    raise FailClosedError(
        f"silently picking value_a is forbidden: {row.claim!r}")


def pick_b(row: SplitRow) -> None:
    """Refused. Silently picking value_b is forbidden."""
    raise FailClosedError(
        f"silently picking value_b is forbidden: {row.claim!r}")
