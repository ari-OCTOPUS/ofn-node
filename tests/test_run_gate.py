"""HALT lane contract tests — the gate must be able to go RED.

Blueprint §10: halt stops STARTS; in-flight parks to HELD; restart never
resends. Every rule here has a negative control — a gate that cannot
refuse is a decoration.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.adapters.run_gate import RunGate
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.domain import RiskTier
from ofn.kernel.tenancy import TenantId, TenantScope
from ofn.adapters.outbox import Outbox

_NOW = 1780000000
_AC = hashlib.sha256(b"fixture").hexdigest()


def _env(key: str = "idem-gate"):
    return create_envelope(
        goal="gate fixture", risk_tier="GREEN", authority_level="A1",
        idempotency_key=key, acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand="a1b2c3d4e5f6a7b8",
        deadline_iso="2026-09-09T12:00:00Z")


def _scope() -> TenantScope:
    return TenantScope(tenant=TenantId("studio"))


class GateStopsStarts(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        t = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.halt_path = t / "halt.flag"
        self.store = RunStore(t / "runs")
        self.gate = RunGate(self.store, self.halt_path)

    def test_clean_state_starts_runs(self):
        run_id = self.gate.start_run(_env(), now_epoch_s=_NOW)
        self.assertTrue(run_id.startswith("run-"))

    def test_armed_flag_refuses_start_and_writes_nothing(self):
        halt_flag.write_halt(self.halt_path)
        with self.assertRaises(HaltActive):
            self.gate.start_run(_env("burn-check"), now_epoch_s=_NOW)
        self.assertEqual(list(self.store.replay()), [])
        # key not burned: after clear, the same envelope creates fine
        halt_flag.clear_halt(self.halt_path)
        self.assertTrue(self.gate.start_run(_env("burn-check"),
                                            now_epoch_s=_NOW))

    def test_corrupt_flag_refuses_start(self):
        self.halt_path.write_text("garbage!!", encoding="utf-8")
        with self.assertRaises(HaltActive):
            self.gate.start_run(_env(), now_epoch_s=_NOW)

    def test_flag_is_read_before_every_start(self):
        self.assertTrue(self.gate.may_issue_claims())
        halt_flag.write_halt(self.halt_path)
        self.assertFalse(self.gate.may_issue_claims())


class GateAndOutbox(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        t = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.halt_path = t / "halt.flag"
        self.store = RunStore(t / "runs")
        self.outbox = Outbox(str(t / "outbox.db"))
        self.addCleanup(self.outbox.close)  # Windows: release the db file before tmp cleanup
        self.gate = RunGate(self.store, self.halt_path, outbox=self.outbox)

    def _enqueue_one(self, key: str = "k1"):
        scope = _scope()
        self.outbox.enqueue(scope, key, "test_effect",
                            payload={"n": 1}, tier=RiskTier.GREEN,
                            now_iso="2026-09-02T00:00:00Z")
        return scope

    def test_claim_refused_while_halted(self):
        scope = self._enqueue_one()
        halt_flag.write_halt(self.halt_path)
        with self.assertRaises(FailClosedError):
            self.gate.claim(scope, "k1", "2026-09-02T00:00:01Z")

    def test_claim_works_when_clean(self):
        scope = self._enqueue_one()
        self.assertTrue(self.gate.claim(scope, "k1", "2026-09-02T00:00:01Z"))

    def test_in_flight_parks_to_held_under_halt(self):
        scope = self._enqueue_one()
        self.gate.claim(scope, "k1", "2026-09-02T00:00:01Z")
        moved = self.gate.hold_in_flight("2026-09-02T00:00:02Z")
        self.assertEqual(moved, 1)
        held_keys = [i.idem_key for i in self.outbox.held(scope)]
        self.assertIn("k1", held_keys)

    def test_restart_never_resends(self):
        scope = self._enqueue_one()
        self.gate.claim(scope, "k1", "2026-09-02T00:00:01Z")
        # "restart": recovery parks to HELD — and there is no resend knob
        self.gate.recover_after_restart("2026-09-02T00:00:02Z")
        pending_after = [i.idem_key for i in self.outbox.pending(scope)]
        self.assertNotIn("k1", pending_after)   # not re-queued for sending
        held_keys = [i.idem_key for i in self.outbox.held(scope)]
        self.assertIn("k1", held_keys)          # parked for a human


if __name__ == "__main__":
    unittest.main()
