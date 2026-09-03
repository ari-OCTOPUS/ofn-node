"""HALT latch transitions — a second witness of the kill switch.

The flag file is the live switch (I/O adapter). This module is the
kernel-pure history of assert/clear: if the flag and the latch
disagree, that disagreement is visible. Absence of disagreement is
agreement, not inattention.

A recorded transition is not a run. It does not grant
``send_authorized``, ``quote_sent``, or ``campaign_envelope_ready``.
It does not burn an idempotency key. Double-assert and clear-while-
disarmed fail closed so a lost transition cannot hide.

HALT stops STARTS. Recording a latch transition is the switch's
own witness, so this index has no halt parameter.

Not wired into ``halt_flag`` or ``run_gate`` (those files are owned
or already complete on main). The adapter side log
(``ofn.adapters.halt_log``) is the I/O body.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .errors import FailClosedError
from .events import FORBIDDEN_EFFECT_KINDS, is_forbidden_effect_name

HALT_ASSERTED = "HALT_ASSERTED"
HALT_CLEARED = "HALT_CLEARED"

TRANSITION_KINDS = frozenset({HALT_ASSERTED, HALT_CLEARED})

# Hands that may arm or disarm. Widen only with a test.
ACTORS = frozenset({"owner", "supervisor"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A latch transition never authorizes a send. Structurally False."""
    return False


def halt_blocks_latch() -> bool:
    """Structurally False. The transition IS the switch's witness."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} required: {value!r}")
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")
    if value in FORBIDDEN_EFFECT_KINDS:
        raise FailClosedError(
            f"{what} is a sealed effect kind: {value!r}")


def _require_kind(kind: str) -> str:
    _refuse_sealed(kind, what="kind")
    if kind not in TRANSITION_KINDS:
        raise FailClosedError(f"unknown latch kind: {kind!r}")
    return kind


def _require_actor(actor: str) -> str:
    _refuse_sealed(actor, what="actor")
    if actor not in ACTORS:
        raise FailClosedError(f"unknown latch actor: {actor!r}")
    return actor


def _require_ts(now_epoch_s: object) -> int:
    if not isinstance(now_epoch_s, int) or isinstance(now_epoch_s, bool):
        raise FailClosedError(f"now_epoch_s must be int: {now_epoch_s!r}")
    return now_epoch_s


def _require_note(note: Optional[str]) -> Optional[str]:
    if note is None:
        return None
    if not isinstance(note, str) or not note.strip():
        raise FailClosedError(f"note must be a non-empty string or None: {note!r}")
    _refuse_sealed(note, what="note")
    return note


def make_transition(
    *,
    kind: str,
    now_epoch_s: int,
    actor: str,
    note: Optional[str] = None,
) -> dict:
    """Build one latch-transition record. This is not a run event."""
    kind = _require_kind(kind)
    ts = _require_ts(now_epoch_s)
    actor = _require_actor(actor)
    note = _require_note(note)
    rec: Dict[str, object] = {
        "kind": kind,
        "ts": ts,
        "actor": actor,
        "note": note,
    }
    return rec


class LatchIndex:
    """Append-only in-memory assert/clear history. Replay does not write.

    Armed state is derived from the recorded sequence, not from a
    caller-supplied flag. ``disagrees_with_flag`` is the second
    witness: the flag and the latch are compared, never assumed equal.
    """

    def __init__(self) -> None:
        self._order: List[dict] = []
        self._armed: bool = False

    def armed(self) -> bool:
        return self._armed

    def __len__(self) -> int:
        return len(self._order)

    def may_record(self, kind: str) -> bool:
        """True only when this kind is the legal next transition."""
        kind = _require_kind(kind)
        if kind == HALT_ASSERTED:
            return not self._armed
        return self._armed

    def record(self, rec: dict) -> int:
        """Append one checked transition. Returns the new length.

        Double-assert and clear-while-disarmed fail closed. A
        hand-built dict is re-validated through ``make_transition``.
        """
        if not isinstance(rec, dict):
            raise FailClosedError(f"latch record must be a mapping: {rec!r}")
        kind = rec.get("kind")
        ts = rec.get("ts")
        actor = rec.get("actor")
        note = rec.get("note")
        if not isinstance(kind, str):
            raise FailClosedError(f"kind required: {kind!r}")
        if not isinstance(ts, int) or isinstance(ts, bool):
            raise FailClosedError(f"now_epoch_s must be int: {ts!r}")
        if not isinstance(actor, str):
            raise FailClosedError(f"actor required: {actor!r}")
        if note is not None and not isinstance(note, str):
            raise FailClosedError(f"note must be a non-empty string or None: {note!r}")
        checked = make_transition(
            kind=kind, now_epoch_s=ts, actor=actor, note=note,
        )
        kind = checked["kind"]
        if kind == HALT_ASSERTED and self._armed:
            raise FailClosedError(
                "HALT_ASSERTED while latch already armed — "
                "missing HALT_CLEARED is a discrepancy, not a no-op")
        if kind == HALT_CLEARED and not self._armed:
            raise FailClosedError(
                "HALT_CLEARED while latch not armed — "
                "stray clear is not an owner decision")
        # Snapshot: mutating a caller dict must not mutate the index.
        self._order.append({
            "kind": checked["kind"],
            "ts": checked["ts"],
            "actor": checked["actor"],
            "note": checked["note"],
        })
        self._armed = kind == HALT_ASSERTED
        return len(self._order)

    def replay(self) -> Tuple[dict, ...]:
        """Read-only copy. Mutating the snapshot does not write."""
        return tuple(dict(rec) for rec in self._order)

    def disagrees_with_flag(self, flag_halted: object) -> bool:
        """True when the live flag and the latch history disagree.

        ``flag_halted`` is a bool supplied by the caller (the adapter
        reads the file). A non-bool is UNKNOWN, not False.
        """
        if type(flag_halted) is not bool:
            raise FailClosedError(
                f"flag_halted must be a bool (UNKNOWN is not False): "
                f"{flag_halted!r}")
        return self._armed != flag_halted
