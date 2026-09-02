"""HALT lane contract tests — the gate must be able to go RED.

Blueprint §10: halt stops STARTS; in-flight parks to HELD; restart never
resends. Every rule here has a negative control — a gate that cannot
refuse is a decoration. Round-2 (evidence-hardening): unknown storage,
atomic transition, HELD recovery, no-resend across ALL entry points,
bounded backoff.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.adapters.run_gate import RunGate
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.kernel.domain import RiskTier
from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError
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
        self.addCleanup(self.outbox.close)  # Windows: release db before tmp cleanup
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


class EvidenceHardeningRound(unittest.TestCase):
    """Directive round 2: unknown storage, atomic transition, HELD
    recovery, no-resend across ALL entry points, bounded backoff."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        t = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.halt_path = t / "halt.flag"
        self.store = RunStore(t / "runs")
        self.outbox = Outbox(str(t / "outbox.db"))
        self.addCleanup(self.outbox.close)
        self.gate = RunGate(self.store, self.halt_path, outbox=self.outbox)

    # ── unknown storage ─────────────────────────────────────────────
    def test_binary_garbage_flag_halts(self):
        raw = bytes([0x00, 0xFF, 0xFE, 0x01]) + b"garbage"
        self.halt_path.write_bytes(raw)
        self.assertTrue(halt_flag.halt_flag_active(self.halt_path))
        with self.assertRaises(HaltActive):
            self.gate.start_run(_env("binkey"), now_epoch_s=_NOW)

    def test_utf16_bom_flag_halts_fail_closed(self):
        # a UTF-16LE "0" — a naive text reader would mis-parse it as OFF;
        # our parser must treat mojibake as HALTED, not as "running".
        raw = bytes([0xFF, 0xFE]) + "0".encode("utf-16-le")
        self.halt_path.write_bytes(raw)
        self.assertTrue(halt_flag.halt_flag_active(self.halt_path))

    # ── atomic transition ───────────────────────────────────────────
    def test_write_halt_is_canonical_and_atomic_final_state(self):
        halt_flag.write_halt(self.halt_path)
        self.assertEqual(self.halt_path.read_text(encoding="utf-8"), "1\n")
        self.assertFalse(list(self.halt_path.parent.glob("*.tmp")),
                         "atomic replace must leave no temp litter")
        # decision flips in one step: refuse → clear → allow
        with self.assertRaises(HaltActive):
            self.gate.start_run(_env("atom1"), now_epoch_s=_NOW)
        halt_flag.clear_halt(self.halt_path)
        self.assertTrue(self.gate.start_run(_env("atom1"), now_epoch_s=_NOW))

    # ── HELD recovery ───────────────────────────────────────────────
    def test_held_item_not_claimable_and_not_pending(self):
        scope = _scope()
        self.outbox.enqueue(scope, "held1", "test_effect",
                            payload={"n": 1}, tier=RiskTier.GREEN,
                            now_iso="2026-09-02T00:00:00Z")
        self.gate.claim(scope, "held1", "2026-09-02T00:00:01Z")
        self.gate.hold_in_flight("2026-09-02T00:00:02Z")
        self.assertNotIn("held1",
                         [i.idem_key for i in self.outbox.pending(scope)])
        self.assertFalse(
            self.gate.claim(scope, "held1", "2026-09-02T00:00:03Z"),
            "HELD must not be claimable without a human decision")
        # approve_manual is deliberately PENDING-only: a HELD item (send
        # status unknown) can never slide into an auto-approval path.
        self.assertFalse(self.outbox.approve_manual(
            scope, "held1", "2026-09-02T00:04:00Z", approved_by="owner"))
        # the real human decision on a HELD item: explicit resolve/fail
        # (mark_failed returns None — the LEDGER is the truth, not the return)
        self.outbox.mark_failed(
            scope, "held1", "2026-09-02T00:05:00Z",
            note="owner reviewed crash-recovered item: do not send")
        self.assertNotIn("held1",
                         [i.idem_key for i in self.outbox.held(scope)])

    def test_no_resend_across_all_entry_points_attempts_unchanged(self):
        scope = _scope()
        self.outbox.enqueue(scope, "nr1", "test_effect",
                            payload={"n": 1}, tier=RiskTier.GREEN,
                            now_iso="2026-09-02T00:00:00Z")
        self.gate.claim(scope, "nr1", "2026-09-02T00:00:01Z")
        # every entry point that could resurface work:
        self.gate.recover_after_restart("2026-09-02T00:00:02Z")   # 1. restart
        self.gate.hold_in_flight("2026-09-02T00:00:03Z")          # 2. explicit hold
        halt_flag.write_halt(self.halt_path)                      # 3. halt on
        with self.assertRaises(HaltActive):                       # 4. start under halt
            self.gate.start_run(_env("nr-new"), now_epoch_s=_NOW)
        with self.assertRaises(FailClosedError):                  # 5. claim under halt
            self.gate.claim(scope, "nr1", "2026-09-02T00:00:04Z")
        pending_keys = [i.idem_key for i in self.outbox.pending(scope)]
        self.assertNotIn("nr1", pending_keys)                     # never re-queued
        item = [i for i in self.outbox.held(scope) if i.idem_key == "nr1"][0]
        self.assertEqual(item.attempts, 1)  # recovery never bumps attempts

    # ── bounded retry ───────────────────────────────────────────────
    def test_backoff_schedule_exact_and_capped(self):
        from ofn.kernel import source_health as sh
        self.assertEqual(sh.backoff_delays(), (1, 2, 4))
        capped = sh.backoff_delays(attempts=10, cap_s=60)
        self.assertTrue(all(d <= 60 for d in capped))
        self.assertEqual(len(capped), 10)


class HaltFlagDurabilityAndSymlink(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.flag = Path(self._tmp.name) / "halt.flag"

    def test_write_halt_file_is_0600_on_posix(self):
        if os.name == "nt":
            self.skipTest("POSIX file mode is not a Windows fact")
        halt_flag.write_halt(self.flag)
        self.assertEqual(self.flag.stat().st_mode & 0o777, 0o600)
        self.assertTrue(halt_flag.halt_flag_active(self.flag))

    def test_symlink_flag_halts_without_following(self):
        target = Path(self._tmp.name) / "not-a-flag"
        target.write_text("off\n", encoding="utf-8")
        self.flag.symlink_to(target)
        # The target says "off" (running). Following it would be a miss.
        self.assertTrue(halt_flag.halt_flag_active(self.flag))

    def test_dangling_symlink_halts(self):
        self.flag.symlink_to(Path(self._tmp.name) / "missing")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))

    def test_write_halt_replaces_a_symlink_with_a_regular_file(self):
        target = Path(self._tmp.name) / "elsewhere"
        target.write_text("off\n", encoding="utf-8")
        self.flag.symlink_to(target)
        halt_flag.write_halt(self.flag)
        self.assertFalse(self.flag.is_symlink())
        self.assertTrue(self.flag.is_file())
        self.assertEqual(target.read_text(encoding="utf-8"), "off\n")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))


if __name__ == "__main__":
    unittest.main()
