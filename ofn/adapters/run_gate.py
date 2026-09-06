"""run_gate — the scheduler's thin, loud wrapper (HALT lane).

The blueprint's layer-3 rule, wired end to end: the flag is read BEFORE
RUN_CREATED, not after. While halted: no run starts, no claim is issued,
in-flight outbox work parks to HELD, and a restart NEVER resends —
`recover_after_restart()` calls `recover_stale(resend=False)` with no
parameter to flip, because "resend" is a decision this module refuses to
own. Halt stops STARTS; what already left the door is a human's question
with context, which is exactly what HELD means in the outbox.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ofn.adapters import halt_flag
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.kernel.envelope import TaskEnvelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.rejection import make_rejection
from ofn.kernel.tenancy import TenantScope


class RunGate:
    def __init__(self, store: RunStore, halt_path: Path,
                 outbox=None, reject_log=None) -> None:
        self._store = store
        self._halt_path = Path(halt_path)
        self._outbox = outbox  # optional: claim/hold wiring needs it
        self._reject_log = reject_log  # optional: RUN_REJECTED side log

    # ── the flag ────────────────────────────────────────────────────────
    def halted(self) -> bool:
        return halt_flag.halt_flag_active(self._halt_path)

    # ── starts ──────────────────────────────────────────────────────────
    def start_run(self, envelope: TaskEnvelope, *, now_epoch_s: int) -> str:
        """Read the flag BEFORE the store writes anything. A refused start
        leaves no half-born run and burns no idempotency key.

        When a ``reject_log`` is wired, a HALT-refused start is recorded
        as ``RUN_REJECTED`` on that side ledger — never on the run
        store. Unwired callers keep the previous behaviour (raise only).
        """
        if self.halted() and self._reject_log is not None:
            self._reject_log.record(make_rejection(
                run_id=envelope.run_id,
                reason="halt_active",
                now_epoch_s=now_epoch_s,
                idempotency_key=envelope.idempotency_key,
            ))
        return self._store.create(
            envelope, halted=self.halted(), now_epoch_s=now_epoch_s)

    # ── claims ──────────────────────────────────────────────────────────
    def may_issue_claims(self) -> bool:
        return not self.halted()

    def claim(self, scope: TenantScope, idem_key: str, now_iso: str) -> bool:
        if self.halted():
            raise FailClosedError(
                "kill_switch: claim refused — no new work leaves while halted")
        if self._outbox is None:
            raise FailClosedError("run_gate has no outbox wired for claims")
        return self._outbox.claim(scope, idem_key, now_iso)

    # ── containment & restart ───────────────────────────────────────────
    def hold_in_flight(self, now_iso: str) -> int:
        """Halt parks in-flight work to HELD: send status unknown, needs a
        human decision — the outbox's own semantics, unchanged."""
        if self._outbox is None:
            raise FailClosedError("run_gate has no outbox wired to hold")
        return self._outbox.recover_stale(now_iso, resend=False)

    def recover_after_restart(self, now_iso: str) -> int:
        """Restart never resends. No `resend` parameter exists here on
        purpose: enabling resend is a per-transport decision that belongs
        to the transport's owner, not to the recovery path."""
        return self.hold_in_flight(now_iso)
