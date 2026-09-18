"""Pin a classified four-state result onto a caller-owned run_id.

The pin records (run_id → result). Same pair is already_pinned.
A different result on the same run is result_collision.
peek never writes.

A pinned passed label is not send_authorized. Ready is not
authorized. Missing is UNKNOWN (None), not FALSE.

Distinct from receipts, receipt_bind, settlement, send_fence,
campaign_bind, and release_pipeline. Not wired into run_store.py.
HALT stops STARTS, not this pin.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Dict, Optional

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .result_class import (
    PASSED,
    classify_result,
    grants_send as result_grants_send,
)


def grants_send() -> bool:
    """A state pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def pin_allows_send() -> bool:
    """Structurally False. A pinned passed label is not a send."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Not wired into the run store."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def _run_id(value: object) -> str:
    if type(value) is not str or not RUN_ID_RE.match(value):
        raise FailClosedError(f"run_id required: {value!r}")
    return value


class StatePin:
    """Caller-owned (run_id → result) map. Replay / peek do not write."""

    def __init__(self) -> None:
        self._pinned: Dict[str, str] = {}

    def peek(self, run_id: object) -> Optional[str]:
        """Read without writing. Missing run is None, not FALSE."""
        rid = _run_id(run_id)
        return self._pinned.get(rid)

    def pin(
        self,
        run_id: object,
        result: object,
        *,
        sent: object = None,
        ok: object = None,
    ) -> str:
        """Record a classified result. Second same pair is already_pinned."""
        rid = _run_id(run_id)
        labeled = classify_result(result, sent=sent, ok=ok)
        if labeled is None:
            raise FailClosedError(
                "result missing — UNKNOWN is not a pin")
        prior = self._pinned.get(rid)
        if prior is None:
            self._pinned[rid] = labeled
            return "pinned"
        if prior == labeled:
            return "already_pinned"
        raise FailClosedError(
            f"result_collision run={rid!r} have={prior!r} got={labeled!r}")

    def try_pin(
        self,
        run_id: object,
        result: object,
        *,
        sent: object = None,
        ok: object = None,
    ) -> Optional[str]:
        """Missing result is UNKNOWN (None). Present-but-bad fails closed."""
        if result is None:
            return None
        return self.pin(run_id, result, sent=sent, ok=ok)


def pin_allows_passed_only(label: object) -> bool:
    """True only for the passed label. Still does not grant a send."""
    if label is None:
        return False
    if type(label) is not str:
        raise FailClosedError(f"label must be a str or None: {label!r}")
    if result_grants_send() or grants_send():
        raise FailClosedError("result/pin drifted into granting send")
    return label == PASSED
