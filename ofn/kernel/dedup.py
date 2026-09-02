"""(kind, ref) duplicate-delivery predicate.

The store refuses a second append of the same (kind, ref). That rule
lives inline in an adapter another open change already owns. This
module is the kernel-pure second witness: if two deliveries bind to
the same (kind, ref), the second is refused. Events without a ref
are not distinguishable duplicates — their idempotency rides on the
envelope key, not this index.

A remembered pair is not send_authorized, quote_sent, or
campaign_envelope_ready.

HALT stops STARTS. This index has no halt parameter: in-flight
duplicate detection must still work so recovery does not need the
owner.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Optional, Set, Tuple

from .errors import FailClosedError
from .events import EVENT_KINDS, FORBIDDEN_EFFECT_KINDS, is_forbidden_effect_name


def grants_send() -> bool:
    """A duplicate-delivery index never authorizes a send. Structurally False."""
    return False


def halt_blocks_dedup() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight dedup."""
    return False


def _require_kind(kind: str) -> str:
    if not isinstance(kind, str) or not kind.strip():
        raise FailClosedError(f"kind required: {kind!r}")
    if kind in FORBIDDEN_EFFECT_KINDS or is_forbidden_effect_name(kind):
        raise FailClosedError(
            f"forbidden effect kind: {kind!r} — ready/authorized/sent "
            "are not ledger events")
    if kind not in EVENT_KINDS:
        raise FailClosedError(f"unknown event kind: {kind!r}")
    return kind


def _tracked_ref(ref: Optional[str]) -> Optional[str]:
    """Empty / None ref is not a distinguishable duplicate.

    Matches the store: only a non-empty ref participates in (kind, ref).
    """
    if ref is None:
        return None
    if not isinstance(ref, str):
        raise FailClosedError(f"ref must be a string or None: {ref!r}")
    if not ref.strip():
        return None
    if is_forbidden_effect_name(ref):
        raise FailClosedError(
            f"ref names a sealed send/ready state: {ref!r}")
    return ref


class KindRefIndex:
    """Append-only in-memory (kind, ref) set. Replay does not write."""

    def __init__(self) -> None:
        self._seen: Set[Tuple[str, str]] = set()
        self._order: list[Tuple[str, str]] = []

    def seen(self, kind: str, ref: Optional[str]) -> bool:
        """True only when this exact tracked pair was recorded."""
        kind = _require_kind(kind)
        tracked = _tracked_ref(ref)
        if tracked is None:
            return False
        return (kind, tracked) in self._seen

    def remember(self, kind: str, ref: Optional[str]) -> bool:
        """Record a tracked pair. Empty ref is a no-op (returns False).

        A second remember of the same pair fails closed — one delivery,
        one effect. Returns True when a new pair was recorded.
        """
        kind = _require_kind(kind)
        tracked = _tracked_ref(ref)
        if tracked is None:
            return False
        pair = (kind, tracked)
        if pair in self._seen:
            raise FailClosedError(
                f"duplicate event rejected: {kind} ref={tracked!r} already recorded")
        self._seen.add(pair)
        self._order.append(pair)
        return True

    def __len__(self) -> int:
        return len(self._order)

    def replay(self) -> Tuple[Tuple[str, str], ...]:
        """Read-only snapshot in append order. Has no write path."""
        return tuple(self._order)
