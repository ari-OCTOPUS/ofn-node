"""RUN_REJECTED — a refused start is a fact, not a run.

``events.RUN_REJECTED`` exists so the halt layer can record a refused
start without creating a run. The run store will not accept this kind
(it is not a run event). This module is the kernel-pure second witness:

  * ``make_rejection`` builds one vocabulary record
  * ``RefusalIndex`` is an in-memory append-only list of those records

Neither grants ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. A rejection is a trace that a start did
not happen. It does not burn an idempotency key and it does not block
a later start of the same envelope after HALT is cleared.

HALT stops STARTS. Recording the refusal is the halt's witness, so
this index has no halt parameter — a refusal must still record so
recovery does not need the owner.

Not wired into ``run_store.py`` (owned by an open change). The adapter
side log (``ofn.adapters.reject_log``) is the I/O body.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import RUN_REJECTED, is_forbidden_effect_name, make_event

# A start is refused for one named reason. Widen only with a test.
REFUSAL_REASONS = frozenset({"halt_active"})

# "sent" / "authorized" / "ready" are not refusal reasons or identities.
_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A refusal record never authorizes a send. Structurally False."""
    return False


def blocks_later_start() -> bool:
    """Structurally False. A recorded refusal does not burn the key."""
    return False


def halt_blocks_rejection() -> bool:
    """Structurally False. The refusal IS the halt's witness."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} required: {value!r}")
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")


def make_rejection(
    *,
    run_id: str,
    reason: str,
    now_epoch_s: int,
    idempotency_key: str,
) -> dict:
    """Build one RUN_REJECTED record. The store must not receive this.

    ``run_id`` is the envelope's already-minted identity — the start
    that did not happen. ``reason`` is a closed vocabulary. Ready /
    authorized / sent names are refused as reason, key, or id.
    """
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        raise FailClosedError(
            f"rejection run_id not boundary-minted: {run_id!r}")
    _refuse_sealed(run_id, what="run_id")
    if reason not in REFUSAL_REASONS:
        raise FailClosedError(f"unknown refusal reason: {reason!r}")
    _refuse_sealed(reason, what="reason")
    _refuse_sealed(idempotency_key, what="idempotency_key")
    return make_event(
        RUN_REJECTED,
        run_id,
        now_epoch_s=now_epoch_s,
        payload={"reason": reason, "idempotency_key": idempotency_key},
    )


class RefusalIndex:
    """Append-only in-memory list of start refusals. Replay does not write.

    Duplicate attempts are recorded (each try is a fact). The index
    never refuses a later start — that decision lives at the gate.
    """

    def __init__(self) -> None:
        self._order: List[dict] = []

    def note(self, record: dict) -> int:
        """Append one validated refusal. Returns the new length."""
        if not isinstance(record, dict):
            raise FailClosedError(
                f"refusal record must be a mapping: {record!r}")
        kind = record.get("kind")
        if kind != RUN_REJECTED:
            raise FailClosedError(
                f"RefusalIndex accepts only RUN_REJECTED, not {kind!r}")
        run_id = record.get("run_id")
        payload = record.get("payload") or {}
        if not isinstance(payload, dict):
            raise FailClosedError(
                f"refusal payload must be a mapping: {payload!r}")
        reason = payload.get("reason")
        key = payload.get("idempotency_key")
        # Re-validate through the factory so a hand-built dict cannot
        # smuggle a sealed name or an unknown reason.
        checked = make_rejection(
            run_id=run_id if isinstance(run_id, str) else "",
            reason=reason if isinstance(reason, str) else "",
            now_epoch_s=record.get("ts") if isinstance(record.get("ts"), int)
            and not isinstance(record.get("ts"), bool) else 0,
            idempotency_key=key if isinstance(key, str) else "",
        )
        self._order.append({
            "kind": checked["kind"],
            "run_id": checked["run_id"],
            "ts": checked["ts"],
            "payload": dict(checked["payload"]),
            "ref": checked.get("ref"),
        })
        return len(self._order)

    def count_for(self, run_id: str) -> int:
        _refuse_sealed(run_id, what="run_id")
        return sum(1 for r in self._order if r["run_id"] == run_id)

    def __len__(self) -> int:
        return len(self._order)

    def replay(self) -> Tuple[dict, ...]:
        """Read-only snapshot in note order. Has no write path."""
        return tuple(
            {
                "kind": r["kind"],
                "run_id": r["run_id"],
                "ts": r["ts"],
                "payload": dict(r["payload"]),
                "ref": r.get("ref"),
            }
            for r in self._order
        )

    def last_reason(self, run_id: str) -> Optional[str]:
        _refuse_sealed(run_id, what="run_id")
        for record in reversed(self._order):
            if record["run_id"] == run_id:
                return record["payload"]["reason"]
        return None
