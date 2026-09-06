"""Monotonic sequence cursor — second witness of the store's seq gate.

The store refuses a gap or a replay (expected N, got something else).
That check lives inline in an adapter another open change already owns.
This module is the kernel-pure copy: first accepted seq is 1; each
later accept must equal the next expected value.

Not wired into the run store. Accepting a seq is not send_authorized,
quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This cursor has no halt parameter: in-flight
appends must still be sequenced so recovery does not need the owner.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import List, Tuple

from .errors import FailClosedError
from .events import is_forbidden_effect_name

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A sequence cursor never authorizes a send. Structurally False."""
    return False


def halt_blocks_seq() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight sequencing."""
    return False


class SeqCursor:
    """Append-only monotonic cursor. Replay does not write.

    Two independent claims:

      * first accept must be 1 (the store's ``_expected_seq`` start)
      * every later accept must equal ``next_expected`` — gap and
        replay are the same refusal
    """

    def __init__(self) -> None:
        self._expected = 1
        self._accepted: List[int] = []

    @property
    def next_expected(self) -> int:
        return self._expected

    def accept(self, seq: int) -> int:
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
            raise FailClosedError(
                f"seq missing or invalid: {seq!r}")
        if seq != self._expected:
            raise FailClosedError(
                f"seq gap or replay: expected {self._expected}, got {seq!r}")
        self._accepted.append(seq)
        self._expected = seq + 1
        return seq

    def peek_would_accept(self, seq: int) -> bool:
        """True only when ``accept(seq)`` would succeed. Does not write."""
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
            return False
        return seq == self._expected

    def __len__(self) -> int:
        return len(self._accepted)

    def replay(self) -> Tuple[int, ...]:
        """Read-only snapshot in append order. Has no write path."""
        return tuple(self._accepted)


def refuse_sealed_seq_label(label: object) -> None:
    """A seq is a number. A send/ready name is not a sequence label."""
    if not isinstance(label, str):
        raise FailClosedError(f"seq label must be a string: {label!r}")
    if is_forbidden_effect_name(label) or label.strip().lower() in _SEALED:
        raise FailClosedError(
            f"seq label names a sealed send/ready state: {label!r}")
