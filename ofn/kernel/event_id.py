"""Boundary-minted event identity + append-only uniqueness.

The store stamps ``event_id`` inline (``evt-`` + eight random bytes as
hex). That mint lives in an adapter another open change already owns.
This module is the kernel-pure second witness: the kernel formats; it
does not generate. A reused id is a collision, not a replay.

Not wired into the run store. An event id is not send_authorized,
quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This index has no halt parameter: in-flight identity
checks must still work so recovery does not need the owner.

Kernel purity: hashlib unused; re + typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple

from .errors import FailClosedError
from .events import is_forbidden_effect_name

EVENT_ID_RE = re.compile(r"^evt-[a-f0-9]{16}$")

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An event-id index never authorizes a send. Structurally False."""
    return False


def halt_blocks_event_id() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight identity."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")


def mint_event_id(rand: str) -> str:
    """Format an event_id from boundary-supplied randomness.

    The kernel formats; it does not generate. ``rand`` must be exactly
    sixteen lowercase hex characters — os.urandom(8).hex() at the call
    site is the intended shape, matching the store's adapter mint.
    """
    if not isinstance(rand, str):
        raise FailClosedError(f"rand must be a string: {rand!r}")
    _refuse_sealed(rand, what="rand")
    event_id = f"evt-{rand}"
    if not EVENT_ID_RE.match(event_id):
        raise FailClosedError(f"refusing malformed event_id: {event_id!r}")
    return event_id


def require_event_id(event_id: str) -> str:
    """Validate a store-or-factory minted event_id. Fail closed otherwise."""
    if not isinstance(event_id, str) or not event_id.strip():
        raise FailClosedError(f"event_id required: {event_id!r}")
    _refuse_sealed(event_id, what="event_id")
    if not EVENT_ID_RE.match(event_id):
        raise FailClosedError(f"event_id not boundary-minted: {event_id!r}")
    return event_id


class EventIdIndex:
    """Append-only in-memory set of event identities. Replay does not write.

    A second record of the same id is a collision — event ids are minted
    once. Unlike a receipt binding, there is no "same contract" replay.
    """

    def __init__(self) -> None:
        self._seen: Set[str] = set()
        self._order: List[str] = []

    def record(self, event_id: str) -> str:
        event_id = require_event_id(event_id)
        if event_id in self._seen:
            raise FailClosedError(
                f"duplicate event_id: {event_id!r} — identity collision, "
                "not a replay")
        self._seen.add(event_id)
        self._order.append(event_id)
        return event_id

    def seen(self, event_id: str) -> bool:
        event_id = require_event_id(event_id)
        return event_id in self._seen

    def get(self, event_id: str) -> Optional[str]:
        event_id = require_event_id(event_id)
        return event_id if event_id in self._seen else None

    def __len__(self) -> int:
        return len(self._order)

    def replay(self) -> Tuple[str, ...]:
        """Read-only snapshot in append order. Has no write path."""
        return tuple(self._order)
