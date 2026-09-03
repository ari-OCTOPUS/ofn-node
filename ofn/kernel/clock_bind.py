"""Bind a supplied epoch to a UTC_Z stamp. No clock is read.

Missing epoch or stamp is UNKNOWN (None), not 0 and not FALSE.
Bool/float/str epoch fail closed. Stamp must classify UTC_Z —
OFFSET is not UTC.

The pair is recorded; it does not grant send, promote ready, or
prove concurrent writing. A timeout is not a bind.

campaign_envelope_ready, send_authorized, and quote_sent stay
distinct sealed names and are refused as stamps.

Not wired into run_store.py. HALT stops STARTS, not a bind.

Kernel purity: dataclasses + typing. No datetime, no I/O, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import deadline_epoch_s, require_epoch_s
from .errors import FailClosedError
from .utc_class import UTC_Z, UNKNOWN, classify_stamp


def grants_send() -> bool:
    """A clock bind never authorizes a send. Structurally False."""
    return False


def halt_blocks_bind() -> bool:
    """Structurally False. HALT stops STARTS, not clock binding."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A bind is not filesystem immutability."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def unknown_epoch_is_zero() -> bool:
    """Structurally False. Missing epoch is UNKNOWN, not 0."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A recorded pair is not an external effect."""
    return False


@dataclass(frozen=True)
class ClockBind:
    """One epoch + UTC_Z stamp pair. Frozen so a later write cannot
    silently retcon the recorded instant.
    """

    epoch_s: int
    stamp: str
    stamp_class: str


def bind_clock(epoch_s: object, stamp: object) -> ClockBind:
    """Require both sides. Malformed or OFFSET fails closed.

    Explicit bind is not try_bind: missing is not softened to UNKNOWN
    here. Call try_bind when absence must stay UNKNOWN.
    """
    epoch = require_epoch_s(epoch_s, "epoch_s")
    klass = classify_stamp(stamp)
    if klass == UNKNOWN:
        raise FailClosedError("stamp missing — UNKNOWN is not a bind")
    if klass != UTC_Z:
        raise FailClosedError(
            f"stamp class {klass!r} is not UTC_Z — OFFSET is not UTC")
    if type(stamp) is not str:
        raise FailClosedError(f"stamp must be a str: {stamp!r}")
    return ClockBind(epoch_s=epoch, stamp=stamp.strip(), stamp_class=klass)


def try_bind(epoch_s: object, stamp: object) -> Optional[ClockBind]:
    """Missing either side is UNKNOWN (None). Malformed fails closed.

    None is not 0. None is not FALSE. A present-but-bad value still
    fails closed — unknown shape is not a default instant.
    """
    if epoch_s is None or stamp is None:
        return None
    return bind_clock(epoch_s, stamp)


def pair_agrees(epoch_s: object, stamp: object) -> Optional[bool]:
    """True when both name the same unix second.

    Missing either side is UNKNOWN (None), not False. A bind that
    exists but names two different seconds is False — that is a
    measured disagreement, not a missing witness.
    """
    bound = try_bind(epoch_s, stamp)
    if bound is None:
        return None
    return deadline_epoch_s(bound.stamp) == bound.epoch_s
