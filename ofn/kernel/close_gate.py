"""Append-after-close — second witness of the store's close state.

The store refuses every append once a run is closed, including a
``RUN_CLOSED`` that carries a causal ref. That rule lives inline in an
adapter another open change already owns. This module is the kernel-pure
copy: close is a state change, not a "ref-less event".

Not wired into the run store. Closing a run is not send_authorized,
quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This gate has no halt parameter: in-flight close
and append-after-close must still work so recovery does not need the
owner. A closed run can be left behind; a fresh start is a different
run_id.

Kernel purity: typing only. No json, no clock, no I/O.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A close gate never authorizes a send. Structurally False."""
    return False


def halt_blocks_close() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight close."""
    return False


def _require_run_id(run_id: object) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise FailClosedError(f"run_id required: {run_id!r}")
    if is_forbidden_effect_name(run_id) or run_id.strip().lower() in _SEALED:
        raise FailClosedError(
            f"run_id names a sealed send/ready state: {run_id!r}")
    if not RUN_ID_RE.match(run_id):
        raise FailClosedError(f"run_id not boundary-minted: {run_id!r}")
    return run_id


def _require_ref(ref: Optional[str]) -> Optional[str]:
    """A causal ref is optional. Empty / None is not a second close key.

    Close is a state change even when a ref is present — the store
    paid for this: an ``elif`` that skipped RUN_CLOSED-with-ref left
    the run open.
    """
    if ref is None:
        return None
    if not isinstance(ref, str):
        raise FailClosedError(f"ref must be a string or None: {ref!r}")
    if not ref.strip():
        return None
    if is_forbidden_effect_name(ref) or ref.strip().lower() in _SEALED:
        raise FailClosedError(
            f"ref names a sealed send/ready state: {ref!r}")
    return ref


class CloseGate:
    """Append-only in-memory open/closed map. Replay does not write.

    Two independent claims:

      * note_open   — a run must exist before it can close or append
      * note_closed — close marks the run closed even when a ref is set;
                      a second close is append-after-close
    """

    def __init__(self) -> None:
        # run_id -> closed?
        self._runs: Dict[str, bool] = {}
        self._order: List[str] = []

    def note_open(self, run_id: str) -> bool:
        """Register an open run. Re-noting an open run is idempotent.

        Re-noting a *closed* run fails closed — close is not undone
        by a second open of the same id (recovery starts a new run).
        Returns True on first note, False on a no-op re-note.
        """
        run_id = _require_run_id(run_id)
        if run_id in self._runs:
            if self._runs[run_id]:
                raise FailClosedError(
                    f"append_after_close REJECTED: {run_id!r} — "
                    "recovery starts a new run_id, it does not reopen")
            return False
        self._runs[run_id] = False
        self._order.append(run_id)
        return True

    def note_closed(self, run_id: str, *, ref: Optional[str] = None) -> None:
        """Mark closed. A causal ref does not keep the run open."""
        run_id = _require_run_id(run_id)
        _require_ref(ref)  # validated, then ignored — close is the state
        if run_id not in self._runs:
            raise FailClosedError(
                f"close of unknown run: {run_id!r}")
        if self._runs[run_id]:
            raise FailClosedError(
                f"append_after_close REJECTED: {run_id!r}")
        self._runs[run_id] = True

    def is_closed(self, run_id: str) -> bool:
        run_id = _require_run_id(run_id)
        return bool(self._runs.get(run_id))

    def known(self, run_id: str) -> bool:
        run_id = _require_run_id(run_id)
        return run_id in self._runs

    def may_append(self, run_id: str) -> bool:
        """True only for a known, still-open run. Does not write."""
        run_id = _require_run_id(run_id)
        if run_id not in self._runs:
            return False
        return not self._runs[run_id]

    def refuse_append(self, run_id: str) -> None:
        """Fail closed for unknown or closed. Open runs pass."""
        run_id = _require_run_id(run_id)
        if run_id not in self._runs:
            raise FailClosedError(f"unknown run: {run_id!r}")
        if self._runs[run_id]:
            raise FailClosedError(
                f"append_after_close REJECTED: {run_id!r}")

    def __len__(self) -> int:
        return len(self._order)

    def replay(self) -> Tuple[Tuple[str, bool], ...]:
        """Read-only snapshot in open-note order. Has no write path."""
        return tuple((rid, self._runs[rid]) for rid in self._order)
